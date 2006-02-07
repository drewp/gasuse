from __future__ import division
import math, datetime
from twisted.application import internet, service
from nevow import appserver
from nevow import inevow, loaders, rend, static, url, tags as T
from nevow.tags import Tag
from rdflib.sparql import getLiteralValue
from rdflib import Literal

def floatOrLiteral(x):
    if isinstance(x, Literal):
        return getLiteralValue(x)
    return x

class LineGraph(rend.Page):
    """pts are (x,y), where x could be date like '2006-01-02'"""
    def __init__(self, pts):
        self.pts = pts
        self.xrange = min(pts)[0], max(pts)[0]
        ys = [p[1] for p in pts]
        self.yrange = min(ys), max(ys)
        print "width", self.xrange, self.xwidth()
    def beforeRender(self, ctx):
        inevow.IRequest(ctx).setHeader("Content-Type",
                                       "image/svg+xml; charset=UTF-8")

    def xfloat(self, x):
        if isinstance(x, Literal):
            x = getLiteralValue(x)
            
        if isinstance(x, (datetime.date, datetime.datetime)):
            return float(x.strftime("%s"))
        
        return x
    
    def xwidth(self):
        """as float, uses seconds for days"""
        return self.xfloat(self.xrange[1]) - self.xfloat(self.xrange[0])

    def trans(self, pt):
        xfrac = (self.xfloat(pt[0])
                 - self.xfloat(self.xrange[0])) / self.xwidth()

        return (25 + 835 * xfrac,
                240 - 240 * (pt[1] - self.yrange[0]) /
                (self.yrange[1] - self.yrange[0]))

    def render_tics(self, ctx, data):
        elts = []
        elts.extend([Tag("line")(x1=25, y1=15, x2=25, y2=240),
                     Tag("line")(x1=25, y1=240, x2=840, y2=240)])
        x = floatOrLiteral(self.xrange[0])
        lastPxTic = -100
        while x <= floatOrLiteral(self.xrange[1]):
            px, py = self.trans((x,self.yrange[0]))
            if px > lastPxTic + 30:
                lastPxTic = px
                try:
                    xfmt = "%.1f" % x
                except TypeError:
                    xfmt = str(x)
                elts.append(Tag("text")(x=px, y=240+4, style="text-anchor:middle;dominant-baseline:text-before-edge;font-size:7pt;font-family:helvetica;")[Tag("tspan")[xfmt]])
            elts.append(Tag("line")(x1=px, y1=240, x2=px, y2=240+3))
            dx = self.xwidth() / 30
            if isinstance(x, (datetime.date, datetime.datetime)):
                dx = datetime.datetime.fromtimestamp(dx) - datetime.datetime.fromtimestamp(0)
            oldx = x
            x = x + dx
            if x == oldx:
                raise ValueError("x is stuck at %r, dx=%r" % (x, dx))

        y = self.yrange[0]
        while y <= self.yrange[1]:
            px, py = self.trans((self.xrange[0],y))
            elts.append(Tag("line")(x1=25 - 4, y1=py, x2=25, y2=py))
            elts.append(Tag("text")(x=25-4, y=py, style="text-anchor:end;dominant-baseline:middle;font-size:7pt;font-family:helvetica;")[Tag("tspan")["%.1f" % y]])
            y += .2 / (self.yrange[1] - self.yrange[0])
            
        for pt in self.pts:
            px, py = self.trans(pt)
            elts.append(Tag("line")(style="stroke-width:.1",
                                    x1=px, y1=240,
                                    x2=px, y2=py))
        return elts

    def render_line(self, ctx, data):
        d = ""
        for pt in self.pts:
            if pt is self.pts[0]:
                d += "M "
            elif pt is self.pts[1]:
                d += "L "
            d += "%s %s " % self.trans(pt)
        return Tag("path")(stroke="black", fill="none",
                           style="marker-mid:url(#Dot);", d=d)
        
    docFactory = loaders.stan(Tag("svg")(xmlns="http://www.w3.org/2000/svg",
                                         width=850, height=260,
                                         style="stroke-width:1px",
                                         stroke="black")[
        Tag("defs")[Tag("marker")(id="Dot", viewBox="0 0 10 10",
                                  refX=5, refY=5,
                                  markerWidth=5, markerHeight=5,
                                  orient="auto")[
             Tag("circle")(fill="red", cx=5, cy=5, r=4)]],
        Tag("g")(transform="")[
        render_line, render_tics,
        ]])

class MainPage(rend.Page):
    docFactory = loaders.stan(T.html[T.body[
        T.p["svg linegraph demo"],
        Tag("embed")(src="graph", type="image/svg+xml",
                     width=850, height=260)
        ]])
    addSlash = True
    def child_graph(self, ctx):
        return LineGraph([(x,math.sin(x)) for x in range(0,50)])

application = service.Application('')
print __name__
if __name__ in ('__builtin__', '__main__'):
    webServer = internet.TCPServer(8081, appserver.NevowSite(MainPage()))
    webServer.setServiceParent(application)
