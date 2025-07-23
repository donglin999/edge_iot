import unittest
import os
import sys
import tempfile
import json
import signal
import subprocess
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.dirname(__file__))

from core.process_integration import ProcessIntegration, ProcessOutput, ProcessSignalResult

class TestProcessIntegration(unittest.TestCase):
    """ProcessIntegration类的单元测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.integration = ProcessIntegration()
    
    def test_init(self):
        """测试初始化"""
        self.assertIsInstance(self.integration, ProcessIntegration)
        self.assertIsInstance(self.integration.process_configs, dict)
        self.assertIsInstance(self.integration.output_monitors, dict)
        self.assertIsInstance(self.integration.output_callbacks, dict)
        self.assertIsInstance(self.integration.running_processes, dict)
    
    def test_get_default_configs(self):
        """测试获取默认配置"""
        configs = self.integration._get_default_configs()
        
        self.assertIsInstance(configs, dict)
        self.assertIn("modbus_collector", configs)
        self.assertIn("opcua_collector", configs)
        self.assertIn("plc_collector", configs)
        self.assertIn("melseca1enet_collector", configs)
        
        # 检查配置结构
        modbus_config = configs["modbus_collector"]
        self.assertEqual(modbus_config["type"], "modbus")
        self.assertIn("module", modbus_config)
        self.assertIn("class", modbus_config)
        self.assertIn("method", modbus_config)
    
    def test_create_process_command(self):
        """测试创建进程命令"""
        config = {
            "device_ip": "192.168.1.100",
            "device_port": 502,
            "protocol": "modbus"
        }
        
        command = self.integration.create_process_command("modbus_collector", config)
        
        self.assertIsInstance(command, list)
        self.assertEqual(command[0], "python")
        self.assertEqual(command[1], "-c")
        self.assertIn("ModbustcpInflux", command[2])
        self.assertIn("modbustcp_influx", command[2])
    
    def test_create_process_command_invalid_type(self):
        """测试创建无效进程类型的命令"""
        config = {}
        
        with self.assertRaises(ValueError):
            self.integration.create_process_command("invalid_type", config)
    
    @patch('subprocess.Popen')
    def test_start_data_acquisition_process(self, mock_popen):
        """测试启动数据采集进程"""
        # 模拟subprocess.Popen
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.stdout = Mock()
        mock_process.stderr = Mock()
        mock_popen.return_value = mock_process
        
        # 模拟数据采集路径存在
        with patch.object(self.integration, 'data_acquisition_path', '/mock/path'):
            command = ["python", "-c", "print('test')"]
            config = {"test": "config"}
            
            result = self.integration.start_data_acquisition_process("test_process", command, config)
            
            self.assertIsNotNone(result)
            self.assertEqual(result.pid, 12345)
            self.assertIn("test_process", self.integration.running_processes)
    
    def test_start_data_acquisition_process_no_path(self):
        """测试在没有数据采集路径时启动进程"""
        with patch.object(self.integration, 'data_acquisition_path', None):
            command = ["python", "-c", "print('test')"]
            config = {"test": "config"}
            
            result = self.integration.start_data_acquisition_process("test_process", command, config)
            
            self.assertIsNone(result)
    
    def test_set_output_callback(self):
        """测试设置输出回调函数"""
        def test_callback(output):
            pass
        
        self.integration.set_output_callback("test_process", test_callback)
        
        self.assertIn("test_process", self.integration.output_callbacks)
        self.assertEqual(self.integration.output_callbacks["test_process"], test_callback)
    
    def test_remove_output_callback(self):
        """测试移除输出回调函数"""
        def test_callback(output):
            pass
        
        self.integration.set_output_callback("test_process", test_callback)
        self.integration.remove_output_callback("test_process")
        
        self.assertNotIn("test_process", self.integration.output_callbacks)
    
    @patch('psutil.pid_exists')
    @patch('psutil.Process')
    def test_send_process_signal_success(self, mock_process_class, mock_pid_exists):
        """测试成功发送进程信号"""
        mock_pid_exists.return_value = True
        mock_process = Mock()
        mock_process_class.return_value = mock_process
        
        result = self.integration.send_process_signal(12345, signal.SIGTERM, "test_process")
        
        self.assertTrue(result.success)
        self.assertEqual(result.signal_sent, signal.SIGTERM)
        self.assertEqual(result.process_name, "test_process")
        mock_process.terminate.assert_called_once()
    
    @patch('psutil.pid_exists')
    def test_send_process_signal_no_process(self, mock_pid_exists):
        """测试向不存在的进程发送信号"""
        mock_pid_exists.return_value = False
        
        result = self.integration.send_process_signal(12345, signal.SIGTERM, "test_process")
        
        self.assertFalse(result.success)
        self.assertIn("不存在", result.message)
    
    @patch('subprocess.Popen')
    def test_graceful_stop_process(self, mock_popen):
        """测试优雅停止进程"""
        # 设置模拟进程
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process
        
        self.integration.running_processes["test_process"] = mock_process
        
        with patch.object(self.integration, 'send_process_signal') as mock_send_signal:
            mock_send_signal.return_value = ProcessSignalResult(
                success=True,
                message="Signal sent",
                signal_sent=signal.SIGTERM,
                process_name="test_process"
            )
            
            result = self.integration.graceful_stop_process("test_process")
            
            self.assertTrue(result.success)
            self.assertEqual(result.signal_sent, signal.SIGTERM)
            mock_process.wait.assert_called_once()
    
    def test_graceful_stop_process_not_running(self):
        """测试停止未运行的进程"""
        result = self.integration.graceful_stop_process("non_existent_process")
        
        self.assertFalse(result.success)
        self.assertIn("未在运行", result.message)
    
    @patch('subprocess.Popen')
    def test_force_kill_process(self, mock_popen):
        """测试强制终止进程"""
        # 设置模拟进程
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.wait = Mock()
        mock_popen.return_value = mock_process
        
        self.integration.running_processes["test_process"] = mock_process
        
        with patch.object(self.integration, 'send_process_signal') as mock_send_signal:
            # 使用数值9代替SIGKILL以兼容Windows
            kill_signal = 9 if not hasattr(signal, 'SIGKILL') else signal.SIGKILL
            mock_send_signal.return_value = ProcessSignalResult(
                success=True,
                message="Signal sent",
                signal_sent=kill_signal,
                process_name="test_process"
            )
            
            result = self.integration.force_kill_process("test_process")
            
            self.assertTrue(result.success)
            self.assertEqual(result.signal_sent, kill_signal)
            mock_process.wait.assert_called_once()
    
    def test_read_process_config(self):
        """测试读取进程配置文件"""
        # 创建临时配置文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_config = {"test": "config", "value": 123}
            json.dump(test_config, f)
            temp_path = f.name
        
        try:
            config = self.integration.read_process_config(temp_path)
            
            self.assertEqual(config, test_config)
        finally:
            os.unlink(temp_path)
    
    def test_read_process_config_not_found(self):
        """测试读取不存在的配置文件"""
        with self.assertRaises(FileNotFoundError):
            self.integration.read_process_config("/non/existent/path.json")
    
    def test_update_process_config(self):
        """测试更新进程配置文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            test_config = {"updated": "config", "new_value": 456}
            
            result = self.integration.update_process_config(temp_path, test_config)
            
            self.assertTrue(result)
            
            # 验证文件内容
            with open(temp_path, 'r') as f:
                saved_config = json.load(f)
            
            self.assertEqual(saved_config, test_config)
        finally:
            os.unlink(temp_path)
    
    @patch('psutil.Process')
    def test_get_process_status(self, mock_process_class):
        """测试获取进程状态"""
        # 设置模拟进程
        mock_subprocess = Mock()
        mock_subprocess.pid = 12345
        mock_subprocess.poll.return_value = None  # 进程运行中
        
        mock_psutil_process = Mock()
        mock_psutil_process.cpu_percent.return_value = 25.5
        mock_psutil_process.memory_info.return_value = Mock(rss=1024*1024*100)  # 100MB
        mock_psutil_process.create_time.return_value = time.time()
        mock_psutil_process.cmdline.return_value = ["python", "test.py"]
        mock_process_class.return_value = mock_psutil_process
        
        self.integration.running_processes["test_process"] = mock_subprocess
        
        status = self.integration.get_process_status("test_process")
        
        self.assertIsNotNone(status)
        self.assertEqual(status["name"], "test_process")
        self.assertEqual(status["pid"], 12345)
        self.assertEqual(status["status"], "running")
        self.assertEqual(status["cpu_percent"], 25.5)
        self.assertAlmostEqual(status["memory_mb"], 100, places=1)
    
    def test_get_process_status_not_running(self):
        """测试获取未运行进程的状态"""
        status = self.integration.get_process_status("non_existent_process")
        
        self.assertIsNone(status)
    
    def test_is_process_running(self):
        """测试检查进程是否运行"""
        # 设置模拟进程
        mock_process = Mock()
        mock_process.poll.return_value = None  # 进程运行中
        
        self.integration.running_processes["test_process"] = mock_process
        
        self.assertTrue(self.integration.is_process_running("test_process"))
        
        # 测试进程已停止
        mock_process.poll.return_value = 0  # 进程已退出
        self.assertFalse(self.integration.is_process_running("test_process"))
        
        # 测试进程不存在
        self.assertFalse(self.integration.is_process_running("non_existent_process"))
    
    def test_get_available_process_types(self):
        """测试获取可用进程类型"""
        types = self.integration.get_available_process_types()
        
        self.assertIsInstance(types, list)
        self.assertIn("modbus_collector", types)
        self.assertIn("opcua_collector", types)
        self.assertIn("plc_collector", types)
        self.assertIn("melseca1enet_collector", types)
    
    def test_get_process_config_template(self):
        """测试获取进程配置模板"""
        template = self.integration.get_process_config_template("modbus_collector")
        
        self.assertIsNotNone(template)
        self.assertEqual(template["type"], "modbus")
        self.assertIn("module", template)
        self.assertIn("class", template)
        
        # 测试不存在的进程类型
        template = self.integration.get_process_config_template("invalid_type")
        self.assertIsNone(template)
    
    def test_process_output_dataclass(self):
        """测试ProcessOutput数据类"""
        timestamp = datetime.now()
        output = ProcessOutput(
            timestamp=timestamp,
            stream_type="stdout",
            content="Test output",
            process_name="test_process"
        )
        
        self.assertEqual(output.timestamp, timestamp)
        self.assertEqual(output.stream_type, "stdout")
        self.assertEqual(output.content, "Test output")
        self.assertEqual(output.process_name, "test_process")
    
    def test_process_signal_result_dataclass(self):
        """测试ProcessSignalResult数据类"""
        result = ProcessSignalResult(
            success=True,
            message="Signal sent successfully",
            signal_sent=signal.SIGTERM,
            process_name="test_process"
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Signal sent successfully")
        self.assertEqual(result.signal_sent, signal.SIGTERM)
        self.assertEqual(result.process_name, "test_process")

class TestProcessIntegrationIntegration(unittest.TestCase):
    """ProcessIntegration集成测试"""
    
    def setUp(self):
        """测试前的设置"""
        self.integration = ProcessIntegration()
    
    def test_full_process_lifecycle(self):
        """测试完整的进程生命周期"""
        # 这个测试需要实际的project-data-acquisition环境
        # 在没有实际环境的情况下，我们跳过这个测试
        self.skipTest("需要实际的project-data-acquisition环境")
    
    def test_config_file_operations(self):
        """测试配置文件操作"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = os.path.join(temp_dir, "test_config.json")
            
            # 测试配置
            test_config = {
                "device_ip": "192.168.1.100",
                "device_port": 502,
                "protocol": "modbus",
                "tags": [
                    {"name": "tag1", "address": "40001"},
                    {"name": "tag2", "address": "40002"}
                ]
            }
            
            # 更新配置文件
            result = self.integration.update_process_config(config_path, test_config)
            self.assertTrue(result)
            
            # 读取配置文件
            loaded_config = self.integration.read_process_config(config_path)
            self.assertEqual(loaded_config, test_config)

if __name__ == '__main__':
    unittest.main()