import routes
import logging
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.internet.defer import Deferred
from types import FunctionType

class RoutableResource(Resource):
    '''
    Provides routes-like dispatching for twisted.web.server.

    Frequently, it's much easier to describe your website layout using routes
    instead of Resource from twisted.web.resource. This small library lets you
    dispatch with routes in your twisted.web application.

    Usage:

        from twisted.internet import reactor
        from twisted.web.server import Site
        from txsimpleroutes import RoutableResource
        
        # Create a Controller
        class Controller(RoutableResource):
            
            @route('/')
            def index(self, request, **kwargs):
                return '<html><body>Hello World!</body></html>'

            @route('/docs/{item}', conditions=dict(method=['GET']))
            def docs(self, request, item, **kwargs):
                return '<html><body>Docs for %s</body></html>' % item.encode('utf8')

            @route('/docs/{item}', conditions=dict(method=['POST']))
            def post_data(self, request, **kwargs):
                return '<html><body>OK</body></html>'

        factory = Site(Controller())
        reactor.listenTCP(8000, factory)
        reactor.run()

    Helpful background information:
    - Python routes: http://routes.groovie.org/
    - Using twisted.web.resources: http://twistedmatrix.com/documents/current/web/howto/web-in-60/dynamic-dispatch.html
    
    Adopted from txroutes and corepost
    '''
    isLeaf = True

    def __init__(self, logger=logging.getLogger('RoutableResource'), *args, **kwargs):
        Resource.__init__(self)
        self.logger = logger
        self.__mapper = routes.Mapper()
        self.__registerRoutes()
    
    def __registerRoutes(self):
        """
            use meta programming to find all the functions labeled with 
            a route, and add them to the mapper
        """
        self.logger.debug("Registering Routes for %s" % self.__class__ )
        
        for _,func in self.__class__.__dict__.iteritems():
            if type(func) == FunctionType and hasattr(func,'route'):  
                i = 0
                for route in func.route:
                    route_kwargs = func.route_kwargs[i]
                    self.logger.debug("%s - %s - %s" %(func, route, route_kwargs))
                    self.__mapper.connect(route, route, handler=func, **route_kwargs)
                    i +=1
        
    def render_HEAD(self, request):
        return self.__route_request('HEAD', request)

    def render_GET(self, request):
        return self.__route_request('GET', request)

    def render_POST(self, request):
        return self.__route_request('POST', request)

    def render_PUT(self, request):
        return self.__route_request('PUT', request)

    def render_DELETE(self, request):
        return self.__route_request('DELETE', request)

    def __route_request(self, method, request):
        """ route a request to the correct method """

        request_path = '/' + '/'.join(request.postpath)
        
        wsgi_environ = {}
        wsgi_environ['REQUEST_METHOD'] = method
        wsgi_environ['PATH_INFO'] = request_path
        
        # Match the route using groovie's mapper
        result = self.__mapper.match(environ=wsgi_environ)
        
        handler = None

        if result is not None and 'handler' in result:
            handler = result['handler']
            del result['handler']
        
        if handler:
            # parse out the HTTP arguments as well
            kwargs = request.args
            for key,value in result.items():
                kwargs[key]=value
            
            response = handler(self, request, **kwargs)
            
            if response.__class__ == Deferred:
                response.addCallback(self._finish_response, request=request)
                return NOT_DONE_YET
            else:
                if type(response) in [str, unicode]:
                    return response.encode('utf8')
                else:
                    return "%s" % response
        else:
            self.logger.error("No route found for %s" % ('/' + '/'.join(request.postpath)) )
            
            request.setResponseCode(404)
            return '<html><head><title>404 Not Found</title></head>' \
                    '<body><h1>Not found</h1></body></html>'
                    
    def _finish_response(self, response, request=None):
        request.write(response)
        request.finish()        

def route(url, **kwargs):
    """ 
        Define a route for a method
        
            @route('/get/{id}')
            def get(self):
                return "ok"
    """
    
    def decorator(func):
        if getattr(func, 'route', None):
            func.route += [url]
            func.route_kwargs += [kwargs]
        else:
            func.route = [url]
            func.route_kwargs = [kwargs]
        return func

    return decorator


if __name__ == '__main__':
    from twisted.internet import reactor, defer
    import twisted.python.log
    import logging

    logger = logging.getLogger('twisted_routes')
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

    observer = twisted.python.log.PythonLoggingObserver(loggerName='twisted_routes')
    observer.start()
    
    class SimpleTest(RoutableResource):
        
        @route('/')
        def index(self, request, **kwargs):
            return request.path

        @route('/cows/{dug}')
        def cows(self, request, **kwargs):
            return kwargs.get('dug')

        # supports multiple routes to same method
        @route('/test2')          
        @route('/test')
        @defer.inlineCallbacks
        def inline_callbacks(self, request, **kwargs):
            d = defer.Deferred()
            def finish():
                print "done"
                d.callback("done")
                
            reactor.callLater(1, finish)
            result = yield d
            defer.returnValue(result)
            
            
    simple = SimpleTest(logger=logger)
    factory = Site(simple)
    reactor.listenTCP(8088, factory) 

    print "Starting test server on http://localhost:8088"

    reactor.run()                  
    

