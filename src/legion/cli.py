#!/usr/bin/env python3
"""Legion CLI - интерфейс командной строки для управления Legion.

Команды:
  start       - Запустить Legion систему
  stop        - Остановить систему
  status      - Проверить статус системы
  compliance  - Получить compliance отчет
  metrics     - Показать метрики производительности
  agents      - Список активных агентов
"""

import argparse
import asyncio
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    rprint = print

from legion.core import LegionCore
from legion.os_integration import AuditLogger

logger = logging.getLogger(__name__)


class LegionCLI:
    """Интерфейс командной строки для Legion."""
    
    def __init__(self):
        self.console = Console() if RICH_AVAILABLE else None
        self.core: LegionCore | None = None
    
    def print_banner(self):
        """Показать баннер."""
        banner = """
╭────────────────────────────────────────╮
│        LEGION AI SYSTEM v2.2        │
│   Multi-Agent AI Framework       │
╰────────────────────────────────────────╯
        """
        if self.console:
            self.console.print(banner, style="bold cyan")
        else:
            print(banner)
    
    async def start_command(self, args):
        """Запустить Legion систему."""
        rprint("[bold green]▶️  Starting Legion v2.2...[/bold green]")
        
        try:
            config = {
                'num_workers': args.workers,
                'hot_cache_size': args.cache_size,
                'cache_ttl': 3600
            }
            
            self.core = LegionCore(config)
            await self.core.start()
            
            rprint("[bold green]✅ Legion started successfully![/bold green]")
            rprint(f"  Workers: {args.workers}")
            rprint(f"  Cache size: {args.cache_size}")
            rprint(f"  OS Integration: ✅ Enabled")
            
            if not args.detach:
                rprint("\nPress Ctrl+C to stop...")
                try:
                    await asyncio.Event().wait()
                except KeyboardInterrupt:
                    rprint("\n[yellow]⚠️  Received stop signal[/yellow]")
                    await self.core.stop()
                    rprint("[green]✅ Legion stopped[/green]")
        
        except Exception as e:
            rprint(f"[bold red]❌ Error starting Legion: {e}[/bold red]")
            sys.exit(1)
    
    async def stop_command(self, args):
        """Остановить Legion систему."""
        rprint("[yellow]⏸️  Stopping Legion...[/yellow]")
        
        if self.core:
            await self.core.stop()
            rprint("[green]✅ Legion stopped successfully[/green]")
        else:
            rprint("[yellow]⚠️  Legion is not running[/yellow]")
    
    async def status_command(self, args):
        """Проверить статус системы."""
        rprint("[bold cyan]📊 Legion Status Report[/bold cyan]\n")
        
        if not self.core:
            self.core = LegionCore()
        
        try:
            metrics = self.core.get_metrics()
            
            if self.console:
                table = Table(title="System Metrics")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")
                
                table.add_row("Uptime", f"{metrics.get('uptime_seconds', 0):.2f}s")
                table.add_row("Total Tasks", str(metrics.get('total_tasks', 0)))
                table.add_row("Cache Hit Rate", metrics.get('cache_hit_rate', '0%'))
                table.add_row("Cache Hits", str(metrics.get('cache_hits', 0)))
                table.add_row("Cache Misses", str(metrics.get('cache_misses', 0)))
                
                self.console.print(table)
                
                # Agent calls
                agent_calls = metrics.get('agent_calls', {})
                if agent_calls:
                    rprint("\n[bold]Agent Calls:[/bold]")
                    for agent_id, count in agent_calls.items():
                        rprint(f"  {agent_id}: {count}")
            else:
                print(json.dumps(metrics, indent=2))
            
        except Exception as e:
            rprint(f"[red]❌ Error getting status: {e}[/red]")
            sys.exit(1)
    
    async def compliance_command(self, args):
        """Получить compliance отчет."""
        rprint("[bold cyan]📋 Compliance Report[/bold cyan]\n")
        
        try:
            audit_logger = AuditLogger()
            report = audit_logger.get_compliance_report()
            
            if self.console:
                table = Table(title="Audit Summary")
                table.add_column("Metric", style="cyan")
                table.add_column("Count", style="green")
                
                table.add_row("Total Events", str(report.get('total_events', 0)))
                table.add_row("Critical Events", str(report.get('critical_events', 0)))
                table.add_row("Error Events", str(report.get('error_events', 0)))
                
                self.console.print(table)
                
                # Agent statistics
                agent_stats = report.get('agent_stats', {})
                if agent_stats:
                    rprint("\n[bold]Agent Activity:[/bold]")
                    for agent_id, count in agent_stats.items():
                        rprint(f"  {agent_id}: {count} events")
            else:
                print(json.dumps(report, indent=2))
        
        except Exception as e:
            rprint(f"[red]❌ Error generating compliance report: {e}[/red]")
            sys.exit(1)
    
    async def metrics_command(self, args):
        """Показать метрики производительности."""
        rprint("[bold cyan]📈 Performance Metrics[/bold cyan]\n")
        
        if not self.core:
            self.core = LegionCore()
        
        metrics = self.core.get_metrics()
        
        if args.format == 'json':
            print(json.dumps(metrics, indent=2))
        else:
            if self.console:
                self.console.print_json(json.dumps(metrics))
            else:
                print(json.dumps(metrics, indent=2))
    
    async def agents_command(self, args):
        """Список активных агентов."""
        rprint("[bold cyan]🤖 Active Agents[/bold cyan]\n")
        
        if not self.core:
            self.core = LegionCore()
        
        agents = self.core.get_all_agents()
        
        if not agents:
            rprint("[yellow]⚠️  No agents registered[/yellow]")
            return
        
        if self.console:
            table = Table(title=f"Registered Agents ({len(agents)})")
            table.add_column("Agent ID", style="cyan")
            table.add_column("Type", style="green")
            table.add_column("Status", style="yellow")
            
            for agent_id, agent in agents.items():
                agent_type = agent.__class__.__name__
                status = "✅ Active" if getattr(agent, 'is_active', False) else "⏸️  Inactive"
                table.add_row(agent_id, agent_type, status)
            
            self.console.print(table)
        else:
            for agent_id, agent in agents.items():
                print(f"{agent_id}: {agent.__class__.__name__}")


def main():
    """Главная функция CLI."""
    parser = argparse.ArgumentParser(
        description='Legion AI System v2.2 - Multi-Agent Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # start command
    start_parser = subparsers.add_parser('start', help='Start Legion system')
    start_parser.add_argument('-w', '--workers', type=int, default=4, help='Number of workers (default: 4)')
    start_parser.add_argument('-c', '--cache-size', type=int, default=128, help='Hot cache size (default: 128)')
    start_parser.add_argument('-d', '--detach', action='store_true', help='Run in detached mode')
    
    # stop command
    subparsers.add_parser('stop', help='Stop Legion system')
    
    # status command
    subparsers.add_parser('status', help='Check system status')
    
    # compliance command
    subparsers.add_parser('compliance', help='Generate compliance report')
    
    # metrics command
    metrics_parser = subparsers.add_parser('metrics', help='Show performance metrics')
    metrics_parser.add_argument('-f', '--format', choices=['json', 'table'], default='table', help='Output format')
    
    # agents command
    subparsers.add_parser('agents', help='List active agents')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = LegionCLI()
    cli.print_banner()
    
    # Execute command
    command_map = {
        'start': cli.start_command,
        'stop': cli.stop_command,
        'status': cli.status_command,
        'compliance': cli.compliance_command,
        'metrics': cli.metrics_command,
        'agents': cli.agents_command
    }
    
    command_func = command_map.get(args.command)
    if command_func:
        asyncio.run(command_func(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
