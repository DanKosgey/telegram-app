from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import uuid
import json
import csv
import io
from datetime import datetime
import asyncio
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Load environment variables
load_dotenv()

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ForexSignal(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    symbol: str
    action: str  # BUY/SELL
    entry: Optional[float] = None
    zone_low: Optional[float] = None
    zone_high: Optional[float] = None
    tp1: Optional[float] = None
    tp2: Optional[float] = None
    tp3: Optional[float] = None
    sl: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    source_message: str
    group_name: Optional[str] = "Manual Input"
    confidence: Optional[float] = None
    quality_score: Optional[float] = None
    sentiment: Optional[str] = None
    risk_reward_ratio: Optional[float] = None

class MessageInput(BaseModel):
    message: str
    group_name: Optional[str] = "Manual Input"

class SignalAnalytics(BaseModel):
    total_signals: int
    buy_signals: int
    sell_signals: int
    avg_tp_sl_ratio: Optional[float]
    avg_confidence: Optional[float]
    avg_quality_score: Optional[float]
    symbols_breakdown: dict
    groups_breakdown: dict
    daily_breakdown: dict
    sentiment_breakdown: dict
    performance_metrics: dict

# In-memory storage (replace with database later)
signals_db: List[ForexSignal] = []

# Initialize Gemini chat
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

async def analyze_signal_quality(signal_data: dict, original_message: str) -> tuple:
    """Analyze signal quality and market sentiment using Gemini"""
    try:
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"quality-analysis-{uuid.uuid4()}",
            system_message="""You are a professional forex trading analyst. Analyze the given trading signal and provide:

1. Quality Score (0.0-1.0): Based on completeness of data, clear entry/exit levels, proper risk management
2. Market Sentiment: BULLISH, BEARISH, or NEUTRAL based on the signal and current market context
3. Risk/Reward Ratio: Calculate based on entry, TP1, and SL levels

Return ONLY valid JSON format:
{
  "quality_score": 0.85,
  "sentiment": "BULLISH",
  "risk_reward_ratio": 2.5,
  "analysis": "Brief analysis of signal quality and market conditions"
}"""
        ).with_model("gemini", "gemini-1.5-flash")

        analysis_prompt = f"""
Analyze this forex signal:
Signal Data: {json.dumps(signal_data)}
Original Message: {original_message}

Provide quality score, sentiment, and risk/reward analysis.
"""

        user_message = UserMessage(text=analysis_prompt)
        response = await chat.send_message(user_message)
        
        # Clean and parse response
        response_clean = response.strip()
        if "```json" in response_clean:
            response_clean = response_clean.split("```json")[1].split("```")[0].strip()
        elif "```" in response_clean:
            response_clean = response_clean.split("```")[1].split("```")[0].strip()
        
        analysis_data = json.loads(response_clean)
        
        return (
            analysis_data.get("quality_score"),
            analysis_data.get("sentiment"),
            analysis_data.get("risk_reward_ratio")
        )
        
    except Exception as e:
        print(f"Error analyzing signal quality: {e}")
        return None, None, None

async def extract_signal_with_gemini(message: str, group_name: str = "Manual Input") -> Optional[ForexSignal]:
    """Extract forex signal from message using Gemini"""
    try:
        # Create new chat instance for each extraction
        chat = LlmChat(
            api_key=GEMINI_API_KEY,
            session_id=f"signal-extraction-{uuid.uuid4()}",
            system_message="""You are a Forex signal extraction expert. Extract trading signals from messages and return ONLY valid JSON.

Extract these fields from forex trading messages:
- symbol: Currency pair (e.g., EURUSD, GBPJPY)
- action: BUY or SELL
- entry: Entry price (single number)
- zone_low: Lower bound of entry zone (if zone is mentioned)  
- zone_high: Upper bound of entry zone (if zone is mentioned)
- tp1, tp2, tp3: Take profit levels (numbers)
- sl: Stop loss (number)
- confidence: Your confidence in extraction accuracy (0.0-1.0)

Return JSON format:
{
  "symbol": "EURUSD",
  "action": "BUY",
  "entry": 1.0945,
  "zone_low": null,
  "zone_high": null,
  "tp1": 1.0980,
  "tp2": 1.1000, 
  "tp3": 1.1020,
  "sl": 1.0920,
  "confidence": 0.95
}

If no valid signal found, return: {"error": "No valid signal found"}

ONLY return valid JSON, no explanations."""
        ).with_model("gemini", "gemini-1.5-flash")

        user_message = UserMessage(text=f"Extract signal from: {message}")
        response = await chat.send_message(user_message)
        
        # Parse the JSON response
        try:
            # Clean the response - remove markdown formatting if present
            response_clean = response.strip()
            
            # Remove markdown code blocks if present
            if "```json" in response_clean:
                response_clean = response_clean.split("```json")[1].split("```")[0].strip()
            elif "```" in response_clean:
                response_clean = response_clean.split("```")[1].split("```")[0].strip()
            
            signal_data = json.loads(response_clean)
            
            if "error" in signal_data:
                return None
            
            # Get quality analysis
            quality_score, sentiment, risk_reward = await analyze_signal_quality(signal_data, message)
            
            # Create ForexSignal object
            signal = ForexSignal(
                symbol=signal_data.get("symbol", ""),
                action=signal_data.get("action", ""),
                entry=signal_data.get("entry"),
                zone_low=signal_data.get("zone_low"),
                zone_high=signal_data.get("zone_high"),
                tp1=signal_data.get("tp1"),
                tp2=signal_data.get("tp2"),
                tp3=signal_data.get("tp3"),
                sl=signal_data.get("sl"),
                source_message=message,
                group_name=group_name,
                confidence=signal_data.get("confidence"),
                quality_score=quality_score,
                sentiment=sentiment,
                risk_reward_ratio=risk_reward
            )
            
            return signal
            
        except json.JSONDecodeError:
            print(f"Failed to parse JSON response: {response}")
            return None
            
    except Exception as e:
        print(f"Error extracting signal: {e}")
        return None

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "gemini_configured": bool(GEMINI_API_KEY)}

@app.post("/api/extract-signal")
async def extract_signal(input_data: MessageInput):
    """Extract forex signal from message text"""
    try:
        signal = await extract_signal_with_gemini(input_data.message, input_data.group_name)
        
        if signal:
            # Store in memory database
            signals_db.append(signal)
            return {
                "success": True,
                "signal": signal,
                "message": "Signal extracted successfully"
            }
        else:
            return {
                "success": False,
                "signal": None,
                "message": "No valid signal found in the message"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting signal: {str(e)}")

@app.get("/api/signals")
async def get_signals():
    """Get all extracted signals"""
    return {"signals": signals_db}

@app.get("/api/analytics")
async def get_analytics():
    """Get enhanced signal analytics"""
    if not signals_db:
        return SignalAnalytics(
            total_signals=0,
            buy_signals=0,
            sell_signals=0,
            avg_tp_sl_ratio=None,
            avg_confidence=None,
            avg_quality_score=None,
            symbols_breakdown={},
            groups_breakdown={},
            daily_breakdown={},
            sentiment_breakdown={},
            performance_metrics={}
        )
    
    # Calculate basic analytics
    total_signals = len(signals_db)
    buy_signals = len([s for s in signals_db if s.action.upper() == "BUY"])
    sell_signals = len([s for s in signals_db if s.action.upper() == "SELL"])
    
    # Calculate averages
    confidences = [s.confidence for s in signals_db if s.confidence is not None]
    avg_confidence = sum(confidences) / len(confidences) if confidences else None
    
    quality_scores = [s.quality_score for s in signals_db if s.quality_score is not None]
    avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
    
    # Calculate average TP/SL ratio
    tp_sl_ratios = []
    for signal in signals_db:
        if signal.tp1 and signal.sl and signal.entry:
            if signal.action.upper() == "BUY":
                tp_distance = signal.tp1 - signal.entry
                sl_distance = signal.entry - signal.sl
            else:
                tp_distance = signal.entry - signal.tp1
                sl_distance = signal.sl - signal.entry
            
            if sl_distance > 0:
                tp_sl_ratios.append(tp_distance / sl_distance)
    
    avg_tp_sl_ratio = sum(tp_sl_ratios) / len(tp_sl_ratios) if tp_sl_ratios else None
    
    # Symbols breakdown
    symbols_breakdown = {}
    for signal in signals_db:
        symbol = signal.symbol
        if symbol not in symbols_breakdown:
            symbols_breakdown[symbol] = 0
        symbols_breakdown[symbol] += 1
    
    # Groups breakdown
    groups_breakdown = {}
    for signal in signals_db:
        group = signal.group_name or "Unknown"
        if group not in groups_breakdown:
            groups_breakdown[group] = 0
        groups_breakdown[group] += 1
    
    # Daily breakdown
    daily_breakdown = {}
    for signal in signals_db:
        try:
            date = datetime.fromisoformat(signal.timestamp).strftime("%Y-%m-%d")
            if date not in daily_breakdown:
                daily_breakdown[date] = 0
            daily_breakdown[date] += 1
        except:
            continue
    
    # Sentiment breakdown
    sentiment_breakdown = {}
    for signal in signals_db:
        sentiment = signal.sentiment or "UNKNOWN"
        if sentiment not in sentiment_breakdown:
            sentiment_breakdown[sentiment] = 0
        sentiment_breakdown[sentiment] += 1
    
    # Performance metrics
    performance_metrics = {
        "total_symbols": len(symbols_breakdown),
        "total_groups": len(groups_breakdown),
        "signals_per_day": total_signals / max(len(daily_breakdown), 1),
        "buy_sell_ratio": buy_signals / max(sell_signals, 1) if sell_signals > 0 else buy_signals,
        "avg_risk_reward": sum([s.risk_reward_ratio for s in signals_db if s.risk_reward_ratio]) / len([s for s in signals_db if s.risk_reward_ratio]) if any(s.risk_reward_ratio for s in signals_db) else None
    }
    
    return SignalAnalytics(
        total_signals=total_signals,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        avg_tp_sl_ratio=avg_tp_sl_ratio,
        avg_confidence=avg_confidence,
        avg_quality_score=avg_quality_score,
        symbols_breakdown=symbols_breakdown,
        groups_breakdown=groups_breakdown,
        daily_breakdown=daily_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        performance_metrics=performance_metrics
    )

@app.get("/api/export/csv")
async def export_signals_csv():
    """Export signals to CSV format"""
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        headers = [
            'ID', 'Symbol', 'Action', 'Entry', 'Zone Low', 'Zone High',
            'TP1', 'TP2', 'TP3', 'SL', 'Timestamp', 'Group Name',
            'Confidence', 'Quality Score', 'Sentiment', 'Risk Reward Ratio',
            'Source Message'
        ]
        writer.writerow(headers)
        
        # Write data
        for signal in signals_db:
            writer.writerow([
                signal.id,
                signal.symbol,
                signal.action,
                signal.entry,
                signal.zone_low,
                signal.zone_high,
                signal.tp1,
                signal.tp2,
                signal.tp3,
                signal.sl,
                signal.timestamp,
                signal.group_name,
                signal.confidence,
                signal.quality_score,
                signal.sentiment,
                signal.risk_reward_ratio,
                signal.source_message
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=forex_signals.csv"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting CSV: {str(e)}")

@app.get("/api/export/json")
async def export_signals_json():
    """Export signals to JSON format"""
    try:
        # Convert signals to dict format for JSON serialization
        signals_data = [signal.dict() for signal in signals_db]
        
        json_content = json.dumps({
            "export_timestamp": datetime.now().isoformat(),
            "total_signals": len(signals_data),
            "signals": signals_data
        }, indent=2)
        
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=forex_signals.json"}
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting JSON: {str(e)}")

@app.delete("/api/signals/{signal_id}")
async def delete_signal(signal_id: str):
    """Delete a specific signal"""
    global signals_db
    signals_db = [s for s in signals_db if s.id != signal_id]
    return {"message": "Signal deleted successfully"}

@app.delete("/api/signals")
async def clear_all_signals():
    """Clear all signals"""
    global signals_db
    signals_db = []
    return {"message": "All signals cleared successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)