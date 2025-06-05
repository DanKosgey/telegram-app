from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import os
import uuid
import json
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

class MessageInput(BaseModel):
    message: str
    group_name: Optional[str] = "Manual Input"

class SignalAnalytics(BaseModel):
    total_signals: int
    buy_signals: int
    sell_signals: int
    avg_tp_sl_ratio: Optional[float]
    symbols_breakdown: dict
    groups_breakdown: dict

# In-memory storage (replace with database later)
signals_db: List[ForexSignal] = []

# Initialize Gemini chat
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

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
            signal_data = json.loads(response.strip())
            
            if "error" in signal_data:
                return None
                
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
                confidence=signal_data.get("confidence")
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
    """Get signal analytics"""
    if not signals_db:
        return SignalAnalytics(
            total_signals=0,
            buy_signals=0,
            sell_signals=0,
            avg_tp_sl_ratio=None,
            symbols_breakdown={},
            groups_breakdown={}
        )
    
    # Calculate analytics
    total_signals = len(signals_db)
    buy_signals = len([s for s in signals_db if s.action.upper() == "BUY"])
    sell_signals = len([s for s in signals_db if s.action.upper() == "SELL"])
    
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
    
    return SignalAnalytics(
        total_signals=total_signals,
        buy_signals=buy_signals,
        sell_signals=sell_signals,
        avg_tp_sl_ratio=avg_tp_sl_ratio,
        symbols_breakdown=symbols_breakdown,
        groups_breakdown=groups_breakdown
    )

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