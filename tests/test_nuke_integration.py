"""
Tests for Nuke integration components with mocking.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

# Mock nuke module before importing our code
nuke_mock = Mock()
nuke_mock.NUKE_VERSION_STRING = "14.0v5"
nuke_mock.selectedNodes = Mock(return_value=[])
nuke_mock.allNodes = Mock(return_value=[])
nuke_mock.root = Mock()
nuke_mock.createNode = Mock()
nuke_mock.delete = Mock()
nuke_mock.connectNodes = Mock()

# Mock PySide2/Qt components
pyside_mock = Mock()
pyside_mock.QtWidgets = Mock()
pyside_mock.QtCore = Mock()
pyside_mock.QtGui = Mock()

with patch.dict('sys.modules', {
    'nuke': nuke_mock,
    'PySide2': pyside_mock,
    'PySide2.QtWidgets': pyside_mock.QtWidgets,
    'PySide2.QtCore': pyside_mock.QtCore,
    'PySide2.QtGui': pyside_mock.QtGui
}):
    from src.core.panel_manager import PanelManager
    from src.core.session_manager import SessionManager
    from src.core.action_engine import ActionEngine
    from src.nuke_integration.context_analyzer import ContextAnalyzer
    from src.nuke_integration.node_inspector import NodeInspector
    from src.nuke_integration.script_generator import ScriptGenerator
    from src.nuke_integration.action_applier import ActionApplier


class TestContextAnalyzer:
    """Test the Nuke context analyzer."""
    
    @pytest.fixture
    def context_analyzer(self):
        """Create context analyzer for testing."""
        return ContextAnalyzer()
    
    def test_analyze_current_script(self, context_analyzer, mock_nuke_context):
        """Test analyzing current Nuke script context."""
        # Mock Nuke nodes
        mock_read_node = Mock()
        mock_read_node.name.return_value = "Read1"
        mock_read_node.Class.return_value = "Read"
        mock_read_node.knobs.return_value = {"file": Mock(value="/path/to/image.exr")}
        
        mock_blur_node = Mock()
        mock_blur_node.name.return_value = "Blur1"
        mock_blur_node.Class.return_value = "Blur"
        mock_blur_node.knobs.return_value = {"size": Mock(value=10.0)}
        
        with patch('nuke.allNodes', return_value=[mock_read_node, mock_blur_node]):
            with patch('nuke.selectedNodes', return_value=[mock_blur_node]):
                context = context_analyzer.analyze_current_script()
                
                assert "selected_nodes" in context
                assert "all_nodes" in context
                assert "script_info" in context
                assert len(context["selected_nodes"]) == 1
                assert len(context["all_nodes"]) == 2
                assert context["selected_nodes"][0]["name"] == "Blur1"
    
    def test_get_selected_nodes(self, context_analyzer):
        """Test getting selected nodes."""
        mock_node = Mock()
        mock_node.name.return_value = "TestNode"
        mock_node.Class.return_value = "Grade"
        
        with patch('nuke.selectedNodes', return_value=[mock_node]):
            selected = context_analyzer.get_selected_nodes()
            
            assert len(selected) == 1
            assert selected[0]["name"] == "TestNode"
            assert selected[0]["class"] == "Grade"
    
    def test_get_node_connections(self, context_analyzer):
        """Test analyzing node connections."""
        # Create mock nodes with connections
        mock_read = Mock()
        mock_read.name.return_value = "Read1"
        mock_read.Class.return_value = "Read"
        mock_read.dependent.return_value = []
        
        mock_blur = Mock()
        mock_blur.name.return_value = "Blur1"
        mock_blur.Class.return_value = "Blur"
        mock_blur.input.return_value = mock_read
        mock_blur.dependent.return_value = []
        
        mock_read.dependent.return_value = [mock_blur]
        
        with patch('nuke.allNodes', return_value=[mock_read, mock_blur]):
            connections = context_analyzer.get_node_connections()
            
            assert len(connections) >= 1
            # Should find connection from Read1 to Blur1
    
    def test_analyze_script_complexity(self, context_analyzer):
        """Test script complexity analysis."""
        # Mock various node types
        nodes = []
        node_types = ["Read", "Blur", "Grade", "Merge", "Write"]
        
        for i, node_type in enumerate(node_types):
            mock_node = Mock()
            mock_node.name.return_value = f"{node_type}{i+1}"
            mock_node.Class.return_value = node_type
            nodes.append(mock_node)
        
        with patch('nuke.allNodes', return_value=nodes):
            complexity = context_analyzer.analyze_script_complexity()
            
            assert "node_count" in complexity
            assert "node_types" in complexity
            assert "complexity_score" in complexity
            assert complexity["node_count"] == 5
            assert len(complexity["node_types"]) == 5


class TestNodeInspector:
    """Test the Nuke node inspector."""
    
    @pytest.fixture
    def node_inspector(self):
        """Create node inspector for testing."""
        return NodeInspector()
    
    def test_inspect_node(self, node_inspector):
        """Test inspecting a single node."""
        mock_node = Mock()
        mock_node.name.return_value = "Blur1"
        mock_node.Class.return_value = "Blur"
        mock_node.knobs.return_value = {
            "size": Mock(value=10.0),
            "channels": Mock(value="rgba")
        }
        
        info = node_inspector.inspect_node(mock_node)
        
        assert info["name"] == "Blur1"
        assert info["class"] == "Blur"
        assert "properties" in info
        assert info["properties"]["size"] == 10.0
        assert info["properties"]["channels"] == "rgba"
    
    def test_get_node_properties(self, node_inspector):
        """Test getting node properties."""
        mock_node = Mock()
        mock_knobs = {
            "size": Mock(value=5.0),
            "filter": Mock(value="gaussian"),
            "channels": Mock(value="rgb")
        }
        mock_node.knobs.return_value = mock_knobs
        
        properties = node_inspector.get_node_properties(mock_node)
        
        assert properties["size"] == 5.0
        assert properties["filter"] == "gaussian"
        assert properties["channels"] == "rgb"
    
    def test_analyze_node_performance(self, node_inspector):
        """Test node performance analysis."""
        mock_node = Mock()
        mock_node.name.return_value = "ExpensiveNode"
        mock_node.Class.return_value = "Blur"
        
        # Mock performance metrics
        with patch.object(node_inspector, '_get_node_render_time', return_value=2.5):
            with patch.object(node_inspector, '_get_node_memory_usage', return_value=512):
                perf = node_inspector.analyze_node_performance(mock_node)
                
                assert "render_time" in perf
                assert "memory_usage" in perf
                assert perf["render_time"] == 2.5
                assert perf["memory_usage"] == 512
    
    def test_get_node_errors(self, node_inspector):
        """Test getting node errors."""
        mock_node = Mock()
        mock_node.hasError.return_value = True
        mock_node.error.return_value = "File not found"
        
        errors = node_inspector.get_node_errors(mock_node)
        
        assert len(errors) == 1
        assert "File not found" in errors[0]


class TestScriptGenerator:
    """Test the Nuke script generator."""
    
    @pytest.fixture
    def script_generator(self):
        """Create script generator for testing."""
        return ScriptGenerator()
    
    def test_generate_from_description(self, script_generator):
        """Test generating script from natural language description."""
        description = "Create a glow effect with a blur and grade"
        
        script = script_generator.generate_from_description(description)
        
        assert "nodes" in script
        assert "connections" in script
        assert len(script["nodes"]) > 0
        
        # Should contain blur and grade nodes for glow effect
        node_types = [node["type"] for node in script["nodes"]]
        assert "Blur" in node_types
        assert "Grade" in node_types
    
    def test_create_node_network(self, script_generator):
        """Test creating node network from script description."""
        script = {
            "nodes": [
                {"type": "Read", "name": "Read1", "properties": {"file": "input.exr"}},
                {"type": "Blur", "name": "Blur1", "properties": {"size": 10}},
                {"type": "Grade", "name": "Grade1", "properties": {"multiply": 2.0}}
            ],
            "connections": [
                {"from": "Read1", "to": "Blur1"},
                {"from": "Blur1", "to": "Grade1"}
            ]
        }
        
        with patch('nuke.createNode') as mock_create:
            mock_nodes = {}
            for node_desc in script["nodes"]:
                mock_node = Mock()
                mock_node.name.return_value = node_desc["name"]
                mock_nodes[node_desc["name"]] = mock_node
            
            def create_node_side_effect(node_type, name=None):
                return mock_nodes.get(name, Mock())
            
            mock_create.side_effect = create_node_side_effect
            
            with patch('nuke.connectNodes') as mock_connect:
                nodes = script_generator.create_node_network(script)
                
                assert len(nodes) == 3
                assert mock_create.call_count == 3
                assert mock_connect.call_count == 2
    
    def test_generate_common_effects(self, script_generator):
        """Test generating common VFX effects."""
        effects = [
            "glow effect",
            "color correction",
            "edge detection",
            "motion blur"
        ]
        
        for effect in effects:
            script = script_generator.generate_from_description(f"Create a {effect}")
            assert "nodes" in script
            assert len(script["nodes"]) > 0
    
    def test_optimize_node_tree(self, script_generator):
        """Test node tree optimization."""
        # Create a script with redundant nodes
        script = {
            "nodes": [
                {"type": "Read", "name": "Read1"},
                {"type": "Grade", "name": "Grade1", "properties": {"multiply": 1.0}},  # No-op
                {"type": "Grade", "name": "Grade2", "properties": {"multiply": 2.0}},
                {"type": "Write", "name": "Write1"}
            ],
            "connections": [
                {"from": "Read1", "to": "Grade1"},
                {"from": "Grade1", "to": "Grade2"},
                {"from": "Grade2", "to": "Write1"}
            ]
        }
        
        optimized = script_generator.optimize_node_tree(script)
        
        # Should remove or merge redundant nodes
        assert len(optimized["nodes"]) <= len(script["nodes"])


class TestActionEngine:
    """Test the action engine."""
    
    @pytest.fixture
    def action_engine(self):
        """Create action engine for testing."""
        return ActionEngine()
    
    @pytest.mark.asyncio
    async def test_process_response(self, action_engine, mock_nuke_context):
        """Test processing AI response into actions."""
        ai_response = """
        I'll help you create a glow effect. Here's what we need to do:
        
        1. Add a Blur node with size 20
        2. Create a Grade node to boost the brightness
        3. Merge the blurred result with the original
        """
        
        actions = await action_engine.process_response(ai_response, mock_nuke_context)
        
        assert len(actions) > 0
        assert any(action["type"] == "create_node" for action in actions)
        
        # Should identify node creation actions
        blur_actions = [a for a in actions if a.get("node_type") == "Blur"]
        assert len(blur_actions) > 0
    
    @pytest.mark.asyncio
    async def test_execute_actions(self, action_engine):
        """Test executing parsed actions."""
        actions = [
            {
                "type": "create_node",
                "node_type": "Blur",
                "properties": {"size": 10.0},
                "name": "Blur1"
            },
            {
                "type": "create_node", 
                "node_type": "Grade",
                "properties": {"multiply": 2.0},
                "name": "Grade1"
            },
            {
                "type": "connect_nodes",
                "from": "Blur1",
                "to": "Grade1"
            }
        ]
        
        with patch('nuke.createNode') as mock_create:
            with patch('nuke.connectNodes') as mock_connect:
                mock_blur = Mock()
                mock_blur.name.return_value = "Blur1"
                mock_grade = Mock()
                mock_grade.name.return_value = "Grade1"
                
                mock_create.side_effect = [mock_blur, mock_grade]
                
                results = await action_engine.execute_actions(actions)
                
                assert len(results) == 3
                assert all(r["success"] for r in results)
                assert mock_create.call_count == 2
                assert mock_connect.call_count == 1
    
    def test_parse_node_creation(self, action_engine):
        """Test parsing node creation from text."""
        text = "Create a Blur node with size 15 and channels set to rgba"
        
        actions = action_engine.parse_node_creation(text)
        
        assert len(actions) > 0
        blur_action = actions[0]
        assert blur_action["type"] == "create_node"
        assert blur_action["node_type"] == "Blur"
        assert blur_action["properties"]["size"] == 15
        assert blur_action["properties"]["channels"] == "rgba"
    
    def test_parse_property_changes(self, action_engine):
        """Test parsing property changes from text."""
        text = "Set the blur size to 25 and change the filter to gaussian"
        
        actions = action_engine.parse_property_changes(text, "Blur1")
        
        assert len(actions) > 0
        prop_action = actions[0]
        assert prop_action["type"] == "modify_properties"
        assert prop_action["node_name"] == "Blur1"
        assert prop_action["properties"]["size"] == 25
        assert prop_action["properties"]["filter"] == "gaussian"


class TestActionApplier:
    """Test the action applier."""
    
    @pytest.fixture
    def action_applier(self):
        """Create action applier for testing."""
        return ActionApplier()
    
    @pytest.mark.asyncio
    async def test_apply_create_node_action(self, action_applier):
        """Test applying node creation action."""
        action = {
            "type": "create_node",
            "node_type": "Blur",
            "name": "Blur1",
            "properties": {"size": 10.0, "channels": "rgba"}
        }
        
        with patch('nuke.createNode') as mock_create:
            mock_node = Mock()
            mock_node.name.return_value = "Blur1"
            mock_create.return_value = mock_node
            
            result = await action_applier.apply_action(action)
            
            assert result["success"] is True
            assert result["node_name"] == "Blur1"
            mock_create.assert_called_once_with("Blur", "Blur1")
    
    @pytest.mark.asyncio
    async def test_apply_modify_properties_action(self, action_applier):
        """Test applying property modification action."""
        action = {
            "type": "modify_properties",
            "node_name": "Blur1",
            "properties": {"size": 20.0, "filter": "gaussian"}
        }
        
        mock_node = Mock()
        mock_size_knob = Mock()
        mock_filter_knob = Mock()
        mock_node.knobs.return_value = {
            "size": mock_size_knob,
            "filter": mock_filter_knob
        }
        
        with patch('nuke.toNode', return_value=mock_node):
            result = await action_applier.apply_action(action)
            
            assert result["success"] is True
            mock_size_knob.setValue.assert_called_once_with(20.0)
            mock_filter_knob.setValue.assert_called_once_with("gaussian")
    
    @pytest.mark.asyncio
    async def test_apply_connect_nodes_action(self, action_applier):
        """Test applying node connection action."""
        action = {
            "type": "connect_nodes",
            "from": "Read1",
            "to": "Blur1",
            "input_index": 0
        }
        
        mock_read = Mock()
        mock_blur = Mock()
        
        with patch('nuke.toNode') as mock_to_node:
            mock_to_node.side_effect = lambda name: mock_read if name == "Read1" else mock_blur
            
            with patch('nuke.connectNodes') as mock_connect:
                result = await action_applier.apply_action(action)
                
                assert result["success"] is True
                mock_connect.assert_called_once()
    
    def test_validate_action(self, action_applier):
        """Test action validation."""
        valid_action = {
            "type": "create_node",
            "node_type": "Blur",
            "name": "Blur1"
        }
        
        invalid_action = {
            "type": "invalid_type",
            "node_type": "Blur"
        }
        
        assert action_applier.validate_action(valid_action) is True
        assert action_applier.validate_action(invalid_action) is False


class TestPanelManager:
    """Test the panel manager."""
    
    @pytest.fixture
    def panel_manager(self):
        """Create panel manager for testing."""
        return PanelManager()
    
    def test_create_panel(self, panel_manager):
        """Test creating the main panel."""
        with patch('src.ui.main_panel.NukeAIPanel') as mock_panel_class:
            mock_panel = Mock()
            mock_panel_class.return_value = mock_panel
            
            panel = panel_manager.create_panel()
            
            assert panel is not None
            mock_panel_class.assert_called_once()
    
    def test_show_panel(self, panel_manager):
        """Test showing the panel."""
        mock_panel = Mock()
        panel_manager.panel = mock_panel
        
        panel_manager.show_panel()
        
        mock_panel.show.assert_called_once()
    
    def test_hide_panel(self, panel_manager):
        """Test hiding the panel."""
        mock_panel = Mock()
        panel_manager.panel = mock_panel
        
        panel_manager.hide_panel()
        
        mock_panel.hide.assert_called_once()


class TestSessionManager:
    """Test the session manager."""
    
    @pytest.fixture
    def session_manager(self, temp_dir):
        """Create session manager for testing."""
        with patch('src.core.session_manager.SessionManager._get_sessions_dir', return_value=temp_dir):
            return SessionManager()
    
    def test_create_session(self, session_manager):
        """Test creating a new session."""
        session_id = session_manager.create_session("Test Session")
        
        assert session_id is not None
        assert len(session_id) > 0
    
    def test_save_message(self, session_manager):
        """Test saving a message to session."""
        session_id = session_manager.create_session("Test Session")
        
        message = {
            "role": "user",
            "content": "Test message",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        session_manager.save_message(session_id, message)
        
        messages = session_manager.get_session_messages(session_id)
        assert len(messages) == 1
        assert messages[0]["content"] == "Test message"
    
    def test_list_sessions(self, session_manager):
        """Test listing all sessions."""
        session1 = session_manager.create_session("Session 1")
        session2 = session_manager.create_session("Session 2")
        
        sessions = session_manager.list_sessions()
        
        assert len(sessions) >= 2
        session_ids = [s["id"] for s in sessions]
        assert session1 in session_ids
        assert session2 in session_ids
    
    def test_delete_session(self, session_manager):
        """Test deleting a session."""
        session_id = session_manager.create_session("Test Session")
        
        result = session_manager.delete_session(session_id)
        
        assert result is True
        sessions = session_manager.list_sessions()
        session_ids = [s["id"] for s in sessions]
        assert session_id not in session_ids


class TestNukeIntegrationEnd2End:
    """End-to-end integration tests."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_workflow(self, mock_nuke_context):
        """Test complete workflow from context analysis to action execution."""
        # 1. Analyze context
        context_analyzer = ContextAnalyzer()
        with patch('nuke.selectedNodes', return_value=[]):
            with patch('nuke.allNodes', return_value=[]):
                context = context_analyzer.analyze_current_script()
        
        # 2. Process AI response
        action_engine = ActionEngine()
        ai_response = "Create a blur node with size 10 and connect it to the selected node"
        actions = await action_engine.process_response(ai_response, context)
        
        # 3. Apply actions
        action_applier = ActionApplier()
        with patch('nuke.createNode') as mock_create:
            with patch('nuke.connectNodes') as mock_connect:
                mock_node = Mock()
                mock_create.return_value = mock_node
                
                results = []
                for action in actions:
                    result = await action_applier.apply_action(action)
                    results.append(result)
                
                # Should have successfully created and connected nodes
                assert len(results) > 0
                assert any(r.get("success") for r in results)
    
    @pytest.mark.integration
    def test_script_generation_and_execution(self):
        """Test generating and executing a complete script."""
        script_generator = ScriptGenerator()
        action_applier = ActionApplier()
        
        # Generate script for glow effect
        script = script_generator.generate_from_description("Create a glow effect")
        
        with patch('nuke.createNode') as mock_create:
            with patch('nuke.connectNodes') as mock_connect:
                # Mock node creation
                mock_nodes = []
                for node_desc in script["nodes"]:
                    mock_node = Mock()
                    mock_node.name.return_value = node_desc["name"]
                    mock_nodes.append(mock_node)
                
                mock_create.side_effect = mock_nodes
                
                # Execute script
                nodes = script_generator.create_node_network(script)
                
                assert len(nodes) == len(script["nodes"])
                assert mock_create.call_count == len(script["nodes"])


if __name__ == "__main__":
    pytest.main([__file__])