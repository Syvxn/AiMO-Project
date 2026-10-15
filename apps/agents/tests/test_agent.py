"""Tests for agent runtime behavior that does not require model downloads."""

from types import SimpleNamespace

from aimo_agents import runner


def test_graph_cache_reuses_graph_for_same_settings(monkeypatch):
	created = []

	def fake_build_graph(settings):
		graph = object()
		created.append((settings, graph))
		return graph

	monkeypatch.setattr(runner, "build_graph", fake_build_graph)
	monkeypatch.setattr(runner, "_graph", None)
	monkeypatch.setattr(runner, "_graph_settings", None)

	settings = SimpleNamespace(model="test-model")
	first = runner._get_graph(settings)
	second = runner._get_graph(settings)

	assert first is second
	assert len(created) == 1


def test_graph_cache_rebuilds_when_settings_change(monkeypatch):
	created = []

	def fake_build_graph(settings):
		graph = object()
		created.append(settings)
		return graph

	monkeypatch.setattr(runner, "build_graph", fake_build_graph)
	monkeypatch.setattr(runner, "_graph", None)
	monkeypatch.setattr(runner, "_graph_settings", None)

	runner._get_graph(SimpleNamespace(model="first"))
	runner._get_graph(SimpleNamespace(model="second"))

	assert created == [
		SimpleNamespace(model="first"),
		SimpleNamespace(model="second"),
	]