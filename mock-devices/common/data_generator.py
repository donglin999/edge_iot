#!/usr/bin/env python3
"""
通用数据生成器
"""
import random
import math
import time
from typing import Dict, Any, Callable, Optional, List
from abc import ABC, abstractmethod


class DataGenerator(ABC):
    """数据生成器抽象基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化数据生成器
        
        Args:
            config: 生成器配置
        """
        self.config = config
        self.start_time = time.time()
    
    @abstractmethod
    def generate_data(self) -> Dict[int, Any]:
        """生成数据 - 子类必须实现"""
        pass


class SineWaveGenerator(DataGenerator):
    """正弦波数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化正弦波生成器
        
        Args:
            config: 包含amplitude(振幅)、frequency(频率)、offset(偏移)、phase(相位)等参数
        """
        super().__init__(config)
        self.amplitude = config.get('amplitude', 100.0)
        self.frequency = config.get('frequency', 0.1)  # Hz
        self.offset = config.get('offset', 0.0)
        self.phase = config.get('phase', 0.0)
        self.addresses = config.get('addresses', [0])
    
    def generate_data(self) -> Dict[int, Any]:
        """生成正弦波数据"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        data = {}
        for i, address in enumerate(self.addresses):
            # 为不同地址添加不同的相位偏移
            phase_offset = self.phase + (i * math.pi / 4)
            value = self.amplitude * math.sin(2 * math.pi * self.frequency * elapsed_time + phase_offset) + self.offset
            data[address] = int(value) if isinstance(self.amplitude, int) else value
        
        return data


class RandomDataGenerator(DataGenerator):
    """随机数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化随机数生成器
        
        Args:
            config: 包含min_value(最小值)、max_value(最大值)、data_type(数据类型)等参数
        """
        super().__init__(config)
        self.min_value = config.get('min_value', 0)
        self.max_value = config.get('max_value', 100)
        self.data_type = config.get('data_type', 'int')
        self.addresses = config.get('addresses', [0])
    
    def generate_data(self) -> Dict[int, Any]:
        """生成随机数据"""
        data = {}
        for address in self.addresses:
            if self.data_type == 'int':
                value = random.randint(self.min_value, self.max_value)
            elif self.data_type == 'float':
                value = random.uniform(self.min_value, self.max_value)
            elif self.data_type == 'bool':
                value = random.choice([True, False])
            else:
                value = random.randint(self.min_value, self.max_value)
            
            data[address] = value
        
        return data


class StepDataGenerator(DataGenerator):
    """阶跃数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化阶跃数据生成器
        
        Args:
            config: 包含values(值列表)、step_interval(阶跃间隔)等参数
        """
        super().__init__(config)
        self.values = config.get('values', [0, 1])
        self.step_interval = config.get('step_interval', 10.0)  # 秒
        self.addresses = config.get('addresses', [0])
        self.current_step = 0
    
    def generate_data(self) -> Dict[int, Any]:
        """生成阶跃数据"""
        current_time = time.time()
        elapsed_time = current_time - self.start_time
        
        # 计算当前应该在哪个阶跃
        step_index = int(elapsed_time // self.step_interval) % len(self.values)
        
        data = {}
        for address in self.addresses:
            data[address] = self.values[step_index]
        
        return data


class LinearRampGenerator(DataGenerator):
    """线性斜坡数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化线性斜坡生成器
        
        Args:
            config: 包含start_value、end_value、duration、repeat等参数
        """
        super().__init__(config)
        self.start_value = config.get('start_value', 0)
        self.end_value = config.get('end_value', 100)
        self.duration = config.get('duration', 60.0)  # 持续时间（秒）
        self.repeat = config.get('repeat', False)
        self.addresses = config.get('addresses', [0])
    
    def generate_data(self) -> Dict[int, Any]:
        """生成线性斜坡数据"""
        current_time = time.time() - self.start_time
        
        if self.repeat:
            # 重复模式
            cycle_time = current_time % self.duration
        else:
            # 单次模式
            cycle_time = min(current_time, self.duration)
        
        # 计算当前值
        progress = cycle_time / self.duration
        current_value = self.start_value + (self.end_value - self.start_value) * progress
        
        # 生成数据
        data = {}
        for address in self.addresses:
            data[address] = current_value
        
        return data


class CompositeDataGenerator(DataGenerator):
    """复合数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化复合数据生成器
        
        Args:
            config: 包含generators列表的配置
        """
        super().__init__(config)
        self.generators = []
        
        # 创建子生成器
        generators_config = config.get('generators', [])
        for gen_config in generators_config:
            generator = create_data_generator(gen_config)
            if generator:
                self.generators.append(generator)
    
    def generate_data(self) -> Dict[int, Any]:
        """生成复合数据"""
        combined_data = {}
        
        for generator in self.generators:
            data = generator.generate_data()
            combined_data.update(data)
        
        return combined_data


class CustomFunctionGenerator(DataGenerator):
    """自定义函数数据生成器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化自定义函数生成器
        
        Args:
            config: 包含function（函数字符串）等参数
        """
        super().__init__(config)
        self.function_str = config.get('function', 'lambda t: t')
        self.addresses = config.get('addresses', [0])
        
        try:
            # 编译函数
            self.function = eval(self.function_str)
        except Exception as e:
            # 如果函数编译失败，使用默认函数
            self.function = lambda t: 0
    
    def generate_data(self) -> Dict[int, Any]:
        """生成自定义函数数据"""
        current_time = time.time() - self.start_time
        
        try:
            value = self.function(current_time)
        except Exception:
            value = 0
        
        # 生成数据
        data = {}
        for address in self.addresses:
            data[address] = value
        
        return data


def create_data_generator(config: Dict[str, Any]) -> Optional[DataGenerator]:
    """
    数据生成器工厂函数
    
    Args:
        config: 生成器配置
        
    Returns:
        DataGenerator: 数据生成器实例
    """
    if not config:
        return None
    
    generator_type = config.get('type', '').lower()
    
    try:
        if generator_type == 'sine':
            return SineWaveGenerator(config)
        elif generator_type == 'random':
            return RandomDataGenerator(config)
        elif generator_type == 'step':
            return StepDataGenerator(config)
        elif generator_type == 'linear':
            return LinearRampGenerator(config)
        elif generator_type == 'composite':
            return CompositeDataGenerator(config)
        elif generator_type == 'custom':
            return CustomFunctionGenerator(config)
        else:
            print(f"未知的数据生成器类型: {generator_type}")
            return None
    except Exception as e:
        print(f"创建数据生成器时出错: {e}")
        return None 