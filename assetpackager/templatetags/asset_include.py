from django.template import Library, Node, TemplateSyntaxError, resolve_variable
from django.utils.safestring import SafeUnicode
from django.conf import settings

import time

from apps.assetpackager.models import Javascript, CSS, Asset
from apps.assetpackager.jsmin import JavascriptMinify
from apps.assetpackager.csstidy import CSSTidy
#from assetpackager.models import Javascript, CSS, Asset
#from assetpackager.jsmin import JavascriptMinify
#from assetpackager.csstidy import CSSTidy

register = Library()

class JavascriptNode(Node):
    def __init__(self, *args):
        self.filenames = args
        
    def render(self, context):
        self.files = []
        if self.filenames[0] == ":base":
            #Uncomment this if you are not using the Sites Application
            #self.files = Javascript.objects.all()
            self.files = Javascript.on_site.all()
        else:
            self.filenames = ["js/" + name for name in self.filenames]
            #Uncomment this if you are not using the Sites Application
            #self.files = Javascript.objects.filter(javascript__in=self.filenames)
            self.files = Javascript.on_site.filter(javascript__in=self.filenames)
            
        #Ok, we have the files we need to check
        if settings.DEBUG:
            #This prints out each js file individualy
            return self.compute_individual()
        
        #This will output all the files merged into a single file with the Date Attached
        return self.compute_monolithic()
        
    def compute_individual(self):
        ret = ""
        for script in self.files:
            ret += '<script type="text/javascript" src="' + settings.MEDIA_URL + script.javascript + '"></script>' + "\n"
        
        return SafeUnicode(ret)
        
    def compute_monolithic(self):
        ret = ""
        name = "\n".join([script.javascript for script in self.files])
        data = ""
        for script in self.files:
            try:
                f = open(settings.MEDIA_ROOT + script.javascript, "rb")
                data += f.read() + "\n"
            finally:
                f.close()
        _hash = sha(data).hexdigest()
        
        #Uncomment this if you are not using the Sites Application
        #asset = Asset.objects.get_or_create(name=name, asset_type="js")[0]
        asset = Asset.on_site.get_or_create(name=name, asset_type="js")[0]
        
        date = time.mktime(asset.created_on.timetuple())
        
        #Check the Hash
        if asset._hash == _hash:
            #Oh, they are the same, great just give them the existing file
            return '<script type="text/javascript" src="' + settings.MEDIA_URL + "js/base_" + date + '.js"></script>' + "\n"
    
        #The hash has changed so we need to create it.
        try:
            os.remove(settings.MEDIA_ROOT + "js/base_" + date + '.js')
            os.remove(settings.MEDIA_ROOT + "js/base.js")
            f = open(settings.MEDIA_ROOT + "js/base.js", "w")
            f.write(data)
            f.close()
        except:
            pass
        
        asset._hash = _hash
        asset.save()
        #Compute the new date since we saved the asset, thus updated it's date
        date = time.mktime(asset.created_on.timetuple())  
        try:  
            inp = f.open(settings.MEDIA_ROOT + "js/base.js", "r")
            outp = f.open(settings.MEDIA_ROOT + "js/base_" + date + '.js', "w")
            
            jsm = JavascriptMinify()
            jsm.minify(inp, outp)
        finally:
            inp.close()
            outp.close()
        #Ok, the file has beencreated and our hash has been updated, now return the JS code
        return '<script type="text/javascript" src="' + settings.MEDIA_URL + "js/base_" + date + '.js"></script>' + "\n"
        
def javascript_include_merged(parser, token):
    bits = token.contents.split()

    return JavascriptNode(*bits[1:])
javascript_include_merged = register.tag(javascript_include_merged)

class CSSNode(Node):
    def __init__(self, *args):
        self.filenames = args
        
    def render(self, context):
        self.files = []
        if self.filenames[0] == ":base":
            #Uncomment this if you are not using the Sites Application
            #self.files = CSS.objects.all()
            self.files = CSS.on_site.all()
        else:
            self.filenames = ["css/" + name for name in self.filenames]
            #Uncomment this if you are not using the Sites Application
            #self.files = CSS.objects.filter(javascript__in=self.filenames)
            self.files = CSS.on_site.filter(css__in=self.filenames)
            
        #Ok, we have the files we need to check
        if settings.DEBUG:
            #This prints out each js file individualy
            return self.compute_individual()
        
        #This will output all the files merged into a single file with the Date Attached
        return self.compute_monolithic()
        
    def compute_individual(self):
        ret = ""
        for css in self.files:
            ret += '<link href="' + settings.MEDIA_URL + css.css + '" media="screen" rel="Stylesheet" type="text/css" />' + "\n"
        
        return SafeUnicode(ret)
        
    def compute_monolithic(self):
        ret = ""
        name = "\n".join([script.name for script in self.files])
        data = ""
        for css in self.files:
            try:
                f = open(settings.MEDIA_ROOT + css.css, "rb")
                data += f.read() + "\n"
            finally:
                f.close()
        
        _hash = sha(data).hexdigest()
        asset = Asset.on_site.get_or_create(name=name, asset_type="css")[0]
        date = time.mktime(asset.created_on.timetuple())
        if asset._hash == _hash:
            return '<link href="' + settings.MEDIA_URL + "css/base_" + date + '.css" media="screen" rel="Stylesheet" type="text/css" />' + "\n"
    
        #The has has changed so we need to create it.
        try:
            os.remove(settings.MEDIA_ROOT + "css/base_" + date + '.css')
            os.remove(settings.MEDIA_ROOT + "css/base.css")
            f = open(settings.MEDIA_ROOT + "css/base.css", "w")
            f.write(data)
            f.close()
        except:
            pass
        
        asset._hash = _hash
        asset.save()
        date = time.mktime(asset.created_on.timetuple())  
        try:  
            inp = f.open(settings.MEDIA_ROOT + "css/base.css", "r")
            outp = f.open(settings.MEDIA_ROOT + "css/base_" + date + '.css', "w")
            
            tidy = CSSTidy()
            outp.write(tidy.parse(inp.read()))
        finally:
            inp.close()
            outp.close()
        #Ok, the file has beencreated and our hash has been updated, now return the JS code
        return '<link href="' + settings.MEDIA_URL + "css/base_" + date + '.css" media="screen" rel="Stylesheet" type="text/css" />' + "\n"
        
def css_include_merged(parser, token):
    bits = token.contents.split()

    return CSSNode(*bits[1:])
css_include_merged = register.tag(css_include_merged)
            