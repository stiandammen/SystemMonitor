import pytest

from systemmonitor.data.alerts import AlertManager, AlertRule, Alert
from systemmonitor.utils.constants import AlertLevel


@pytest.fixture
def manager(qapp):
    return AlertManager()


def make_rule(metric='test_metric', threshold=50.0, operator='gte', cooldown=0):
    return AlertRule(
        metric=metric,
        threshold=threshold,
        operator=operator,
        level=AlertLevel.WARNING,
        message_template='{metric} is {{value:.1f}} (limit {{threshold:.1f}})'.format(metric=metric),
        cooldown=cooldown,
    )


def test_default_rules_are_loaded(manager):
    rules = manager.get_rules()
    assert len(rules) > 0
    assert any(r.metric == 'cpu_percent' for r in rules.values())


def test_add_and_remove_rule(manager):
    rule = make_rule()
    rule_id = manager.add_rule(rule)
    assert rule_id in manager.get_rules()

    manager.remove_rule(rule_id)
    assert rule_id not in manager.get_rules()


@pytest.mark.parametrize("operator, value, threshold, expected", [
    ('gt', 5, 3, True),
    ('gt', 3, 3, False),
    ('lt', 2, 3, True),
    ('lt', 3, 3, False),
    ('eq', 3, 3, True),
    ('eq', 4, 3, False),
    ('gte', 3, 3, True),
    ('lte', 3, 3, True),
    ('unknown_op', 100, 1, False),
])
def test_check_threshold_operators(manager, operator, value, threshold, expected):
    assert manager._check_threshold(value, threshold, operator) is expected


def test_check_metric_triggers_alert_when_threshold_crossed(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='widget_temp', threshold=50.0, cooldown=0))

    triggered = []
    manager.alert_triggered.connect(triggered.append)
    try:
        manager.check_metric('widget_temp', 75.0)
    finally:
        manager.alert_triggered.disconnect(triggered.append)

    assert len(triggered) == 1
    alert = triggered[0]
    assert isinstance(alert, Alert)
    assert alert.value == 75.0
    assert len(manager.get_active_alerts()) == 1
    assert len(manager.get_alert_history()) == 1


def test_check_metric_does_not_trigger_below_threshold(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='widget_temp', threshold=50.0, cooldown=0))

    triggered = []
    manager.alert_triggered.connect(triggered.append)
    try:
        manager.check_metric('widget_temp', 10.0)
    finally:
        manager.alert_triggered.disconnect(triggered.append)

    assert triggered == []
    assert manager.get_active_alerts() == []


def test_check_metric_respects_cooldown(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='widget_temp', threshold=50.0, cooldown=3600))

    triggered = []
    manager.alert_triggered.connect(triggered.append)
    try:
        manager.check_metric('widget_temp', 80.0)
        manager.check_metric('widget_temp', 80.0)
    finally:
        manager.alert_triggered.disconnect(triggered.append)

    assert len(triggered) == 1


def test_acknowledge_and_clear_alert(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='widget_temp', threshold=50.0, cooldown=0))
    manager.check_metric('widget_temp', 80.0)

    alert_id = next(iter(manager.get_active_alerts())).id
    manager.acknowledge_alert(alert_id)
    assert manager._active_alerts[alert_id].acknowledged is True

    cleared = []
    manager.alert_cleared.connect(cleared.append)
    try:
        manager.clear_alert(alert_id)
    finally:
        manager.alert_cleared.disconnect(cleared.append)

    assert cleared == [alert_id]
    assert manager.get_active_alerts() == []


def test_clear_all_alerts(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='metric_a', threshold=10.0, cooldown=0))
    manager.add_rule(make_rule(metric='metric_b', threshold=10.0, cooldown=0))
    manager.check_metric('metric_a', 50.0)
    manager.check_metric('metric_b', 50.0)
    assert len(manager.get_active_alerts()) == 2

    manager.clear_all_alerts()
    assert manager.get_active_alerts() == []


def test_get_active_alerts_filters_by_level(manager):
    manager._rules.clear()
    warning_rule = AlertRule(metric='m_warn', threshold=10.0, operator='gte',
                             level=AlertLevel.WARNING, message_template='warn {value:.1f}', cooldown=0)
    critical_rule = AlertRule(metric='m_crit', threshold=10.0, operator='gte',
                              level=AlertLevel.CRITICAL, message_template='crit {value:.1f}', cooldown=0)
    manager.add_rule(warning_rule)
    manager.add_rule(critical_rule)
    manager.check_metric('m_warn', 50.0)
    manager.check_metric('m_crit', 50.0)

    assert len(manager.get_active_alerts(level=AlertLevel.WARNING)) == 1
    assert len(manager.get_active_alerts(level=AlertLevel.CRITICAL)) == 1
    assert len(manager.get_active_alerts()) == 2


def test_update_rule_threshold_applies_to_matching_metric(manager):
    manager._rules.clear()
    manager.add_rule(make_rule(metric='shared_metric', threshold=10.0, cooldown=0))
    manager.add_rule(make_rule(metric='shared_metric', threshold=20.0, operator='lt', cooldown=0))
    manager.add_rule(make_rule(metric='other_metric', threshold=5.0, cooldown=0))

    manager.update_rule_threshold('shared_metric', 99.0)

    for rule in manager.get_rules().values():
        if rule.metric == 'shared_metric':
            assert rule.threshold == 99.0
        else:
            assert rule.threshold == 5.0


def test_set_globally_enabled_toggles_all_rules(manager):
    manager.set_globally_enabled(False)
    assert all(not r.enabled for r in manager.get_rules().values())
    manager.set_globally_enabled(True)
    assert all(r.enabled for r in manager.get_rules().values())


def test_enable_rule_toggles_single_rule(manager):
    manager._rules.clear()
    rule_id = manager.add_rule(make_rule(metric='solo_metric', cooldown=0))
    manager.enable_rule(rule_id, False)
    assert manager.get_rules()[rule_id].enabled is False
    manager.enable_rule(rule_id, True)
    assert manager.get_rules()[rule_id].enabled is True
