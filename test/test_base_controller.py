from unittest.mock import Mock, call
from types import SimpleNamespace

from gui.controllers import BaseController
from utils import log


class ConcreteController(BaseController):
    """テスト用の具象コントローラー"""
    def __init__(self):
        super().__init__()
        self.initialized = False
        self.cleaned = False

    def initialize(self):
        self.initialized = True

    def cleanup(self):
        self.cleaned = True

def make_named_mock(name="mock_function"):
    m = Mock()
    # __name__属性を直接追加
    m.__name__ = name
    return m

def test_set_view(monkeypatch):
    controller = ConcreteController()
    dummy_view = SimpleNamespace()

    mocked_log = Mock()
    monkeypatch.setattr(log, "info", mocked_log)

    controller.set_view(dummy_view)

    assert controller._view is dummy_view
    mocked_log.assert_called_once()
    assert "ビューを設定しました" in mocked_log.call_args[0][0]


def test_register_and_trigger_callback(monkeypatch):
    controller = ConcreteController()
    mock_cb = make_named_mock("mock_callback")
    
    mocked_log = Mock()
    monkeypatch.setattr(log, "info", mocked_log)

    controller.register_callback("eventA", mock_cb)
    controller.trigger_callback("eventA", 42, key="value")

    mock_cb.assert_called_once_with(42, key="value")
    assert "eventA" in controller._callbacks
    assert mock_cb in controller._callbacks["eventA"]
    mocked_log.assert_called()


def test_trigger_callback_error(monkeypatch):
    controller = ConcreteController()

    def bad_callback():
        raise ValueError("Test error")

    error_logger = Mock()
    monkeypatch.setattr(log, "error", error_logger)

    controller.register_callback("error_event", bad_callback)
    controller.trigger_callback("error_event")

    error_logger.assert_called()
    assert "コールバック実行エラー" in error_logger.call_args[0][0]


def test_initialize_and_cleanup():
    controller = ConcreteController()
    assert not controller.initialized
    assert not controller.cleaned

    controller.initialize()
    controller.cleanup()

    assert controller.initialized is True
    assert controller.cleaned is True
