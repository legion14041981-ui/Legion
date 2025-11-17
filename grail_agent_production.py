#!/usr/bin/env python3
"""
Grail Agent Production - Production-ready trading agent with Supabase logging
Author: Legion Framework
Date: 2025-11-17
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from supabase import create_client, Client
import random
import time

# Load environment variables
load_dotenv()

class GrailAgentProduction:
    """Production Grail Agent with full logging and error recovery"""
    
    def __init__(self, mode: str = "demo", bankroll: float = 100):
        self.mode = mode
        self.bankroll = bankroll
        self.trades_executed = 0
        self.predictions_logged = 0
        self.total_profit = 0.0
        
        # Setup logging
        self.setup_logging()
        
        # Initialize Supabase
        self.supabase = self.init_supabase()
        
        self.logger.info(f"Grail Agent initialized in {mode} mode with bankroll ${bankroll}")
    
    def setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('grail_agent.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('GrailAgent')
    
    def init_supabase(self) -> Optional[Client]:
        """Initialize Supabase client"""
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                self.logger.warning("Supabase credentials not found. Running without DB logging.")
                return None
            
            client = create_client(url, key)
            self.logger.info("Supabase client initialized successfully")
            return client
        except Exception as e:
            self.logger.error(f"Failed to initialize Supabase: {e}")
            return None
    
    def log_prediction_to_supabase(self, signal: Dict):
        """Log prediction (signal) to Supabase"""
        if not self.supabase:
            return
        
        try:
            prediction_data = {
                'event_name': f"{signal['signal']}_{signal['asset']}",
                'signal': signal['signal'],
                'asset': signal['asset'],
                'confidence': float(signal['confidence']),
                'mode': self.mode,
                'timestamp': signal['timestamp']
            }
            
            self.supabase.table('predictions').insert(prediction_data).execute()
            self.predictions_logged += 1
            self.logger.info(f"Prediction logged to Supabase: {signal['signal']} {signal['asset']} (confidence: {signal['confidence']:.2f})")
        except Exception as e:
            self.logger.error(f"Failed to log prediction to Supabase: {e}")
    
    def log_trade_to_supabase(self, trade_data: Dict):
        """Log trade to Supabase"""
        if not self.supabase:
            return
        
        try:
            self.supabase.table('trades').insert(trade_data).execute()
            self.logger.info(f"Trade logged to Supabase: {trade_data['id']}")
        except Exception as e:
            self.logger.error(f"Failed to log trade to Supabase: {e}")
    
    def generate_signal(self) -> Dict:
        """Generate trading signal (demo implementation)"""
        signal_types = ['BUY', 'SELL', 'HOLD']
        confidence = random.uniform(0.6, 0.95)
        
        return {
            'signal': random.choice(signal_types),
            'confidence': confidence,
            'asset': random.choice(['BTC/USDT', 'ETH/USDT', 'SOL/USDT']),
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_trade(self, signal: Dict) -> Dict:
        """Execute trade based on signal"""
        trade_id = f"trade_{self.trades_executed + 1}_{int(time.time())}"
        
        # Calculate position size (2% of bankroll)
        position_size = self.bankroll * 0.02
        
        # Simulate trade execution
        if self.mode == "demo":
            # Demo mode: simulate random profit/loss
            profit_loss = position_size * random.uniform(-0.05, 0.10)
        else:
            # Live mode: actual trade execution would go here
            self.logger.warning("LIVE MODE: Actual trade execution not implemented yet")
            profit_loss = 0
        
        self.trades_executed += 1
        self.total_profit += profit_loss
        self.bankroll += profit_loss
        
        trade_data = {
            'id': trade_id,
            'signal': signal['signal'],
            'asset': signal['asset'],
            'confidence': signal['confidence'],
            'position_size': position_size,
            'profit_loss': profit_loss,
            'bankroll_after': self.bankroll,
            'mode': self.mode,
            'timestamp': datetime.now().isoformat()
        }
        
        # Log to Supabase
        self.log_trade_to_supabase(trade_data)
        
        self.logger.info(
            f"Trade executed: {signal['signal']} {signal['asset']} | "
            f"P/L: ${profit_loss:.2f} | Bankroll: ${self.bankroll:.2f}"
        )
        
        return trade_data
    
    def run(self, num_predictions: int = 10):
        """Run agent for specified number of predictions"""
        self.logger.info(f"Starting Grail Agent: {num_predictions} predictions")
        
        for i in range(num_predictions):
            try:
                # Generate signal
                signal = self.generate_signal()
                
                # LOG ALL PREDICTIONS (demo mode improvement)
                self.log_prediction_to_supabase(signal)
                
                # Execute trade if confidence > threshold
                if signal['confidence'] > 0.70:
                    trade = self.execute_trade(signal)
                else:
                    self.logger.info(f"Signal confidence too low ({signal['confidence']:.2f}), skipping trade")
                
                # Safety: wait between trades
                time.sleep(1)
                
            except Exception as e:
                self.logger.error(f"Error during prediction {i+1}: {e}")
                continue
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print session summary"""
        roi = (self.total_profit / (self.bankroll - self.total_profit)) * 100 if self.bankroll != self.total_profit else 0
        
        summary = f"""
═══════════════════════════════════════════
📊 GRAIL AGENT SESSION SUMMARY
═══════════════════════════════════════════
Mode: {self.mode.upper()}
Predictions Logged: {self.predictions_logged}
Trades Executed: {self.trades_executed}
Total P/L: ${self.total_profit:.2f}
Final Bankroll: ${self.bankroll:.2f}
ROI: {roi:.2f}%
═══════════════════════════════════════════
"""
        
        self.logger.info(summary)
        print(summary)

def main():
    parser = argparse.ArgumentParser(description='Grail Agent Production')
    parser.add_argument('--mode', type=str, default='demo', choices=['demo', 'live'],
                        help='Trading mode: demo (virtual) or live (real)')
    parser.add_argument('--bankroll', type=float, default=100,
                        help='Initial bankroll amount')
    parser.add_argument('--num-predictions', type=int, default=10,
                        help='Number of predictions to generate')
    
    args = parser.parse_args()
    
    # Initialize and run agent
    agent = GrailAgentProduction(mode=args.mode, bankroll=args.bankroll)
    agent.run(num_predictions=args.num_predictions)

if __name__ == "__main__":
    main()
