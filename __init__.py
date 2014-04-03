################################################################################
#
# SublimeBlender.py
#
# Version: 1.10
# Author: Sven Fraeys
#
# Description: 
# Blende addon, it will process the incoming url request that is launched by sublime
# 
# Free for non-commercial use
#
################################################################################

from urllib.parse import urlparse
import sys, io, traceback, threading, http.server, socketserver, time, urllib, json
import bpy
import importlib
import console

PORT = 8006               # port number, needs to be identical as the Sublime Plugin
IP_ADDRESS = "localhost"  # ip address, needs to be identical as the Sublime Plugin
VERBOSITY = 0              # level of printing (debugging)

def sb_output(message,verbosity=1):
  if verbosity <= VERBOSITY:
      print (message)

class SublimeBlenderCore(object):
  '''core functions
  '''

class SublimeBlenderRequestHandler(http.server.BaseHTTPRequestHandler):
  ''' RequestHandler will process the incoming data
  '''
  verbosity = 0
  def getParameters(self):
    ''' get self._parameters
    '''
    return self._parameters
  
  def setParameters(self, value):
    ''' set self._parameters
    '''
    self._parameters = value
  
  def output(self, message, verbosity=1):
    ''' output a message
    '''
    if verbosity <= self.verbosity:
      print (message)

  def parseUrlToDictionary(self, path):
    '''convert the path to extract the query arguments to a dictionary
    '''
    params = {}
    parsed_path = urlparse(path)
    sb_output('parsed_path=%s' % str(parsed_path) )

    try:
      params = dict([p.split('=') for p in parsed_path[4].split('&')])
    except:
      pass

    for key in params:
      parsedkey = urllib.parse.unquote_plus(params[key])
      sb_output(parsedkey,2)
      params[key] = parsedkey

    return params

  def _writeheaders(self):
    self.send_response(200)
    self.send_header('Content-type', 'text/html; charset=UTF-8')
    self.end_headers()

  def do_HEAD(self):
    self._writeheaders()
    
  def communicate(self, dataDictionary):
    self._writeheaders()
    self.wfile.write(str(json.dumps(dataDictionary) ).encode('latin'))

  def blenderExecuteFile(self,scriptpath):
    sb_output('blenderExecuteFile()')
    sb_output('scriptpath=%s' % scriptpath)
    try:
      pass
      # launch incoming script
      exec(compile(open(scriptpath).read(), scriptpath, 'exec'), globals(), locals() )
      return True
    except:
      print(str(traceback.format_exc()))
      return False
    sb_output('blenderExecuteFile()...done')

  def blenderEval(self,value):
    try:
        eval(vlaue)
    except:
      print(traceback.format_exc())

  def blenderPrint(self, value):
    print(value)

  def blenderDir(self, nameOfObjectToDir):
    sb_output("dir=%s" % nameOfObjectToDir)
    listOfAttributes = ""
    variableObject = None
    found = False
    if nameOfObjectToDir in globals():
      found = True
      variableObject = eval(nameOfObjectToDir)
    else:
      try:
        variableObject = importlib.import_module(nameOfObjectToDir)
        found = True
      except:
        pass
      
    if found:
        # variableObject = eval(nameOfObjectToDir)
        attrs = dir(variableObject)
        for attr in attrs:
          listOfAttributes += attr + ";"
        retstr=listOfAttributes
    else:
      sb_output("not found : %s" % nameOfObjectToDir)

  def blenderConsoleImportComplete(self,nameOfObjectToDir):
    import console.complete_import
    completinglist = console.complete_import.complete(nameOfObjectToDir)
    listOfAttributes = ""
    for attr in completinglist:
      listOfAttributes += attr + ";"
    retstr=listOfAttributes
    return completinglist

  def blenderConsoleCalltipComplete(self,query,namespace):
    nameOfObjectToDir = namespace
    if nameOfObjectToDir in globals():
      variableObject = eval(nameOfObjectToDir)
    else:
      variableObject = importlib.import_module(nameOfObjectToDir)

    if variableObject:
      import console.complete_calltip
      completinglist = console.complete_calltip.complete(query, 999, {nameOfObjectToDir : variableObject})
      sb_output("nameOfObjectToDir=%s" % nameOfObjectToDir)
      sb_output("variableObject=%s" % variableObject)
      sb_output(completinglist)
      retstr = str(completinglist[-1])
      return retstr
    else:
        sb_output("could not find namespace : %s" % namespace )

  def blenderConsoleNamespaceComplete(self,query,namespace):
    import console.complete_namespace
    variableObject = None

    nameOfObjectToDir = namespace
    if nameOfObjectToDir in globals():
      variableObject = eval(nameOfObjectToDir)
    else:
      variableObject = importlib.import_module(nameOfObjectToDir)
    if variableObject:
      completinglist = console.complete_namespace.complete(query, {nameOfObjectToDir : variableObject})
      sb_output("nameOfObjectToDir=%s" % nameOfObjectToDir)
      sb_output("variableObject=%s" % variableObject)
      sb_output("completinglist=%s" % completinglist)
      sb_output("completinglist...done!")
      listOfAttributes = ""

      if len(completinglist) > 101:
        completinglist = completinglist[:100]

      return completinglist
    else:
      sb_output("could not find namespace : %s" % namespace )
      return []

  def do_GET(self):
    # add cube to test behaviour
    # bpy.ops.mesh.primitive_cube_add()

    # global running  
    
    SUBLIME_STDOUT = True

    originalStdOut = None
    newStdOut = None

    
    params = self.parseUrlToDictionary(self.path)

    sb_output('params=%s' % str(params ), 1 )

    self.setParameters(params)

    communicateDictionary = {}

    # print(parsed_path)
    
    retstr = ""

    SUBLIME_STDOUT = True

    
    originalStdOut = sys.stdout
    newStdOut = io.StringIO()
    sys.stdout = newStdOut

    if 'scriptpath' in params:
      scriptpath = params["scriptpath"]
      
      sb_output('#' + scriptpath,1)
      scriptpath = scriptpath.strip()
      if scriptpath != None:
        res = self.blenderExecuteFile(scriptpath)
        communicateDictionary['result'] = res

    if 'eval' in params:
      self.blenderEval(params['eval'])
      
    if "print" in params:
      self.blenderPrint(params["print"])

    if "console_namespace_complete" in params:
      query = params["console_namespace_complete"]
      namespace = params["namespace"]
      res = self.blenderConsoleNamespaceComplete(query, namespace)
      communicateDictionary['result'] = res

    if "console_calltip_complete" in params:
      variableObject = None
      query = params["console_calltip_complete"]
      namespace = params["namespace"]
      res = self.blenderConsoleCalltipComplete(query,namespace)
      communicateDictionary['result'] = res
      
    if "console_import_complete" in params:
      res = self.blenderConsoleImportComplete(params["console_import_complete"])
      communicateDictionary['result'] = res

    if "dir" in params:
      self.blenderDir(params["dir"])

    # restore stdout
    sys.stdout = originalStdOut
    communicateDictionary['stdout'] = (newStdOut.getvalue())
    self.blenderPrint( newStdOut.getvalue() )

    # communicate the collected results
    self.communicate(communicateDictionary)
    
class SublimeBlenderHttpThread(threading.Thread):
  ''' main thread that is looking for signals
  '''
  def __init__(self):
    threading.Thread.__init__(self)
    self.httpd = None

  def run(self):
    
    sb_output("HTTP Server THREAD: started")
    sb_output( "serving at port %s" % PORT)
    self.httpd.serve_forever()
    sb_output("HTTP Server THREAD: finished")
      
class SublimeBlenderControlThread(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    self.httpd = None
  def run(self):
    sb_output("Control THREAD: started")
    runcontrol = 1    
    while runcontrol >0:
      # if running < 1:
      if False:
        sb_output("try server shutdown")
        self.httpd.shutdown()
        self.httpd.socket.close() 
        sb_output("shutdown finished")
        runcontrol = 0
      time.sleep(1)                
        
    sb_output("Control THREAD: finished")
            
class SublimeBlenderOpenConnection(bpy.types.Operator):
    '''SublimeBlender Open Connecion Start
    '''
    bl_idname = "wm.sublimeblenderopenconnection"
    bl_label = "SublimeBlender Open Connection..."
    http_thread = None
    control_thread = None

    def execute(self, context):
        
        httpd = None

        # launch the Request handler
        try:
          httpd = socketserver.TCPServer((IP_ADDRESS, PORT), SublimeBlenderRequestHandler)
          sb_output('Connection open...')
        except:
          pass
          print('FAILED')
          return {'FINISHED'}
        
        sb_output("SCRIPT: started")
        sb_output("httpd: %s" % httpd)

        self.http_thread = SublimeBlenderHttpThread()
        self.http_thread.httpd = httpd
        self.http_thread.start()
        

        self.control_thread = SublimeBlenderControlThread()
        self.control_thread.httpd = httpd
        self.control_thread.start()
        
        sb_output("SCRIPT: finished") 

        return {'FINISHED'}

def register():
    bpy.utils.register_class(SublimeBlenderOpenConnection)

def unregister():
    bpy.utils.unregister_class(SublimeBlenderOpenConnection)
    
if __name__ == "__main__":
    register()

bl_info = {
        "name" : "SublimeBlender",
        "description": "Develop with Sublime Text 3 as an external script editor",
        "category" : "Development",
        "author" : "Sven Fraeys",
        "wiki_url": "https://docs.google.com/document/d/1-hWEdp1Gz4zjyio7Hdc0ZnFXKNB6eusYITnuMI3n65M",
        "version": (1, 1, 0)
}