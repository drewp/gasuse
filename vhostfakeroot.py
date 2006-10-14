from twisted.application import internet, service
from nevow import appserver, vhost
from zope.interface import implements
from nevow import loaders, rend, static, tags as T, inevow

# http://www.divmod.org/trac/wiki/DivmodNevow/Deployment/ReverseProxy
class VhostFakeRoot:
    """
    I am a wrapper to be used at site root when you want to combine 
    vhost.VHostMonsterResource with nevow.guard. If you are using guard, you 
    will pass me a guard.SessionWrapper resource.
    """
    implements(inevow.IResource)
    def __init__(self, wrapped):
        self.wrapped = wrapped
    
    def renderHTTP(self, ctx):
        return self.wrapped.renderHTTP(ctx)
        
    def locateChild(self, ctx, segments):
        """Returns a VHostMonster if the first segment is "vhost". Otherwise
        delegates to the wrapped resource."""
        if segments[0] == "vhost":
            return vhost.VHostMonsterResource(), segments[1:]
        else:
            return self.wrapped.locateChild(ctx, segments)
