"""
A basic implementation of the "visitor pattern" for Python, using decorators.

Inspiration from http://chris-lamb.co.uk/2006/12/08/visitor-pattern-in-python/
which contains a description of such a system but no implementation code that I could find

And http://www.artima.com/weblogs/viewpost.jsp?thread=101605 in which Guido van Rossum
shows how dynamic dispatch ("multi-methods") can be done.

The module has an extra "feature" that by default multiple overloads can be called for a 
class hierarchy, so if you annotated @when(BaseClass) on one method and then @when(Subclass)
on another, and make a call that would invoke the subclass method, then the base class method
is invoked first.

The result of any such "cascaded" superclass call is discarded. If you do not wish a particular
method call to "cascade" before another call to a subclass, use the second annotation argument
ie @when(type, False)

Please don't use this module for evil messes :), only use it when a visitor pattern will actually
eliminate lots of nasty boilerplate code.


Simple example:

@when(str)
def myFunc(arg):
    print "My string has length %d" % (len(arg))
    
@when(int)
def myFunc(arg):
    print "My integer is %d" % arg

myFunc("XYZ")
My string has length 3

myFunc(12)
My integer is 12


Copyright 2011 Angus Gratton. 
"""


# these are the "current" overloaded methods, the @is_visited annotation
# will blat them out again after the current class is defined (allowing multiple
# classes to have mixed overloads with the same method name!)
#
# dict key is function name, value is a method_overload with all the functions named that
# in the class
_methods = {}

class when(object):
    """ Annotation indicating a method is a dynamic dispatch overload. Argument is the type
    of the first function argument,which will be used for dynamic dispatch.    
    
    Arguments:
    argtype - this method should be invoked only with a first argument that matches (or subclasses)
              this type

    allow_cascaded_calls - this method will also be invoked if (default True)

    """
    def __init__(self, argtype, allow_cascaded_calls=True):
        self.argtype = argtype
        self.allow_cascade=allow_cascaded_calls
    def __call__(self, func):
        #print "assigning %s to func %s" % (self.argtype, func)
        self.func_name =func.__name__
        if not self.func_name in _methods:
            _methods[self.func_name] = method_overload(self.func_name)        
        _methods[self.func_name].register(self.argtype, func, self.allow_cascade)
        return _methods[self.func_name]


class method_overload(object):
    """ This is the actual overload information for a particular method
    name on a particular class (or no class.) These are internal,
    created at module import time.

    """
    def __init__(self, func_name):
        self.func_name = func_name
        self.registry = {}
        self.allow_cascade = {}

    def register(self, argtype, func, allow_cascade):
        self.registry[argtype] = func
        self.allow_cascade[argtype] = allow_cascade

    def __get__(self, obj, type=None):
        """ This __get__ is called when the method is bound on a
        class, and returns a bound_caller which knows the instance and
        the class type.

        If the method is not bound on a class, this is skipped and
        __call__ is called directly.

        """
        return bound_caller(self, obj, type)

    def __call__(self, *args, **kw):
        """ This __call__ is only reached when the method is not bound to a class 
        """
        return self.call_internal(lambda f:f, args, kw)

    def call_internal(self, func_modifier, args, kw):
        """ Common utility class for calling an overloaded method,
        either bound on a class or not.  func_modifier is a lambda
        function which is used to "bind" bound methods to the correct
        instance
        """
        argtype = type(args[0])
        hier = list(inspect.getmro(argtype)) # class hierarchy
        hier.reverse() # order w/ superclass first
        hier = [ t for t in hier if t in self.registry ]
        if len(hier) == 0:
            raise TypeError("Function %s has no compatible overloads registered for argument type %s" % 
                            (self.func_name, argtype))            
        result = None
        for t in hier:
            if not self.allow_cascade[t] and t != hier[-1]:
                continue # don't "cascade" down from superclass on this method
            result = func_modifier(self.registry[t])(*args, **kw)
        return result
        

class bound_caller(object):
    """ Temporary class instantiated once(!!!) per method call for
    methods bound to a class, contains the bound instance and its
    class type.

    It may be possible to replace this with a nested function or a
    lambda function, not sure?

    """
    def __init__(self, overload, obj, type):
        self.overload = overload
        self.obj = obj
        self.type = type
        
    def __call__(self, *args, **kw):        
        return self.overload.call_internal(lambda l:l.__get__(self.obj, self.type), args, kw)



def is_visited(cls):
    """ Decorator to mark any class which contains one or more @when annotations.

    This is needed if more than one class/scope in the module contains an overloaded
    method with the same name. If it is missing from a class, the methods on the next
    class will not be distinct from the methods on this class.

    """
    global _methods
    _methods = {}
    return cls

@is_visited
class Sample:

    @when(int)
    def foo(self, a, b):
        print "int %s %d %d" % (self, a,b)

    @when(float)
    def foo(self,a, b, c):
        print "float %s %f %f %f" % (self, a,b,c)

    @when(str)
    def foo(self, a, b):
        print "str %s %s %s" % (self, a,b)


class ClassA(object):
    pass

class ClassB(object):
    pass

class Subclass(ClassA):
    pass

@is_visited
class OtherSample:
    
    @when(ClassA, False)
    def foo(self, a):
        print "foo ClassA %s" % (a)

    @when(ClassB)
    def foo(self, b):
        print "foo ClassB %s" % (b)

    @when(Subclass)
    def foo(self, a):
        print "subclass %s" % (a)


@when(str)
def foo(a,b):
    print "unbound str foo %s %s" % (a, b)

@when(str)
def myFunc(arg):
    print "My string has length %d" % (len(arg))
    
@when(int)
def myFunc(arg):
    print "My integer is %d" % arg
