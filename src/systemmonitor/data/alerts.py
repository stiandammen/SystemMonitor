"""
Alert Manager - System monitoring alerts
"""
import time
from systemmonitor.typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from systemmonitor.enum import Enum
from PyQt6.QtCore import QObject, pyqtSignal

from systemmonitor.utils.constants import AlertLevel
from systemmonitor.i18n import tr


@dataclass
class AlertRule:
    """Alert rule configuration"""
    metric: str
    threshold: float
    operator: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    level: AlertLevel
    message_template: str
    cooldown: int = 30  # seconds
    enabled: bool = True


@dataclass
class Alert:
    """Alert instance"""
    id: str
    rule: AlertRule
    value: float
    timestamp: float
    message: str
    acknowledged: bool = False


class AlertManager(QObject):
    """
    Manages alert rules and triggers alerts when thresholds are crossed
    """
    
    alert_triggered = pyqtSignal(object)  # Alert object
    alert_cleared = pyqtSignal(str)       # Alert ID
    
    def __init__(self):
        super().__init__()
        self._rules: Dict[str, AlertRule] = {}
        self._active_alerts: Dict[str, Alert] = {}
        self._alert_history: List[Alert] = []
        self._last_triggered: Dict[str, float] = {}  # metric -> timestamp
        self._max_history = 100
        
        # Default rules
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default alert rules"""
        default_rules = [
            AlertRule(
                metric='cpu_percent',
                threshold=80.0,
                operator='gte',
                level=AlertLevel.WARNING,
                message_template='CPU usage is {value:.1f}% (threshold: {threshold:.1f}%)',
                cooldown=30
            ),
            AlertRule(
                metric='cpu_percent',
                threshold=95.0,
                operator='gte',
                level=AlertLevel.CRITICAL,
                message_template='CRITICAL: CPU usage is {value:.1f}%!',
                cooldown=10
            ),
            AlertRule(
                metric='memory_percent',
                threshold=85.0,
                operator='gte',
                level=AlertLevel.WARNING,
                message_template='Memory usage is {value:.1f}% (threshold: {threshold:.1f}%)',
                cooldown=30
            ),
            AlertRule(
                metric='memory_percent',
                threshold=95.0,
                operator='gte',
                level=AlertLevel.CRITICAL,
                message_template='CRITICAL: Memory usage is {value:.1f}%!',
                cooldown=10
            ),
            AlertRule(
                metric='disk_percent',
                threshold=90.0,
                operator='gte',
                level=AlertLevel.WARNING,
                message_template='Disk usage is {value:.1f}% (threshold: {threshold:.1f}%)',
                cooldown=60
            ),
            AlertRule(
                metric='gpu_temperature',
                threshold=80.0,
                operator='gte',
                level=AlertLevel.WARNING,
                message_template='GPU temperature is {value:.1f}°C (threshold: {threshold:.1f}°C)',
                cooldown=30
            ),
            AlertRule(
                metric='cpu_temperature',
                threshold=80.0,
                operator='gte',
                level=AlertLevel.WARNING,
                message_template='CPU temperature is {value:.1f}°C (threshold: {threshold:.1f}°C)',
                cooldown=30
            ),
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule) -> str:
        """Add an alert rule"""
        rule_id = f"{rule.metric}_{rule.threshold}_{rule.operator}"
        self._rules[rule_id] = rule
        return rule_id
    
    def remove_rule(self, rule_id: str):
        """Remove an alert rule"""
        if rule_id in self._rules:
            del self._rules[rule_id]
    
    def get_rules(self) -> Dict[str, AlertRule]:
        """Get all alert rules"""
        return self._rules.copy()
    
    def check_metric(self, metric_name: str, value: float):
        """Check a metric value against all applicable rules"""
        for rule_id, rule in self._rules.items():
            if not rule.enabled or rule.metric != metric_name:
                continue
            
            # Check cooldown
            last_triggered = self._last_triggered.get(rule_id, 0)
            if time.time() - last_triggered < rule.cooldown:
                continue
            
            # Check threshold
            triggered = self._check_threshold(value, rule.threshold, rule.operator)
            
            if triggered:
                self._trigger_alert(rule, value)
                self._last_triggered[rule_id] = time.time()
    
    def _check_threshold(self, value: float, threshold: float, operator: str) -> bool:
        """Check if value meets threshold condition"""
        ops = {
            'gt': lambda v, t: v > t,
            'lt': lambda v, t: v < t,
            'eq': lambda v, t: v == t,
            'gte': lambda v, t: v >= t,
            'lte': lambda v, t: v <= t,
        }
        return ops.get(operator, lambda v, t: False)(value, threshold)
    
    def _trigger_alert(self, rule: AlertRule, value: float):
        """Create and emit an alert"""
        alert_id = f"{rule.metric}_{int(time.time())}"
        message = tr(rule.message_template).format(value=value, threshold=rule.threshold)
        
        alert = Alert(
            id=alert_id,
            rule=rule,
            value=value,
            timestamp=time.time(),
            message=message
        )
        
        self._active_alerts[alert_id] = alert
        self._alert_history.append(alert)
        
        # Trim history
        if len(self._alert_history) > self._max_history:
            self._alert_history = self._alert_history[-self._max_history:]
        
        self.alert_triggered.emit(alert)
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        if alert_id in self._active_alerts:
            self._active_alerts[alert_id].acknowledged = True
    
    def clear_alert(self, alert_id: str):
        """Clear an active alert"""
        if alert_id in self._active_alerts:
            del self._active_alerts[alert_id]
            self.alert_cleared.emit(alert_id)
    
    def get_active_alerts(self, level: Optional[AlertLevel] = None) -> List[Alert]:
        """Get active alerts, optionally filtered by level"""
        alerts = list(self._active_alerts.values())
        if level:
            alerts = [a for a in alerts if a.rule.level == level]
        return alerts
    
    def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get alert history"""
        return self._alert_history[-limit:]
    
    def clear_all_alerts(self):
        """Clear all active alerts"""
        for alert_id in list(self._active_alerts.keys()):
            self.clear_alert(alert_id)
    
    def update_rule_threshold(self, metric: str, threshold: float):
        """Update threshold for all rules matching metric"""
        for rule in self._rules.values():
            if rule.metric == metric:
                rule.threshold = threshold
    
    def enable_rule(self, rule_id: str, enabled: bool = True):
        """Enable or disable a rule"""
        if rule_id in self._rules:
            self._rules[rule_id].enabled = enabled

    def set_globally_enabled(self, enabled: bool):
        """Enable or disable all alert rules at once"""
        for rule in self._rules.values():
            rule.enabled = enabled

