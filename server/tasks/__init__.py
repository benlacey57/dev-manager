# tasks/__init__.py - Task module initialization

# Import all task modules for easy access
from . import system
from . import user
from . import ssh
from . import security
from . import docker
from . import dev_tools
from . import web_server
from . import final

__all__ = [
    'system', 'user', 'ssh', 'security', 
    'docker', 'dev_tools', 'web_server', 'final'
]
