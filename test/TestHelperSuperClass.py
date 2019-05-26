import unittest
from executor import executeCommand
import python_Testing_Utilities as testUtils
import json
import time
import os

class testHelperSuperClass(unittest.TestCase):
  kong_server = "TODO" #"http://127.0.0.1:8381"
  def __init__(self, *args, **kwargs):
    super(testHelperSuperClass, self).__init__(*args, **kwargs)
    if "KONGTESTURL" not in os.environ:
      raise Exception("enviroment variable KONGTESTURL not specified")
    self.kong_server = os.environ["KONGTESTURL"]

  def executeCommand(self, cmdToExecute, expectedOutput, expectedErrorOutput, expectedReturnCodes, timeout, skipOutputChecks):

    commandOutputObj = executeCommand(cmdToExecute, timeout)

    correctReturnCode = False
    for x in expectedReturnCodes:
      if x == commandOutputObj.returncode:
        correctReturnCode = True

    def decode_or_none(v):
      if v is None:
        return None
      return v.decode()
    def bytes_to_string(v):
      if v is None:
        return None
      return str(v, "utf-8")


    if not correctReturnCode:
      print("stdOut:" + str(decode_or_none(commandOutputObj.stdout)))
      print("stdErr:" + str(decode_or_none(commandOutputObj.stderr)))
      if commandOutputObj.returncode == -1:
        self.assertFalse(True, msg="Command timeed out and didn't return")
      else:
        self.assertFalse(True, msg="Wrong return code recieved got " + str(commandOutputObj.returncode) + " expected one of " + str(expectedReturnCodes))

    if skipOutputChecks:
      return commandOutputObj

    stdoutString = None
    stdoutString = bytes_to_string(commandOutputObj.stdout)
    stderrString = None
    stderrString = bytes_to_string(commandOutputObj.stderr)

    if (stdoutString is None) and (expectedOutput is None):
      return commandOutputObj
    if stdoutString is None:
      print("Wrong Output: GOT:")
      print("<<<<NONE>>>>")
      print("--------------EXP:")
      print(expectedOutput)
      print("--------------")
      self.assertTrue(False)

    if expectedOutput is None:
      print("Wrong Output: GOT:")
      print(stdoutString)
      print("--------------EXP:")
      print("<<<<NONE>>>>")
      print("--------------")
      self.assertTrue(False)

    if stdoutString.strip().strip('\n') != expectedOutput.strip().strip('\n'):
      print("Wrong Output: GOT:")
      print(stdoutString)
      print("--------------EXP:")
      print(expectedOutput)
      print("--------------")
      self.assertTrue(False)

    self.assertEqual(stderrString,expectedErrorOutput,msg="Wrong Error Output")

    return commandOutputObj

  #api must start with a /
  def callKongService(self, api, headers, method, dataDICT, expectedResponses):
    #print("Calling " + self.kong_server + api + " (" + method + ")")
    resp, respCode = testUtils.callService(self, self.kong_server + api, headers, method, dataDICT, 1, expectedResponses)
    try:
      return json.loads(resp), respCode
    except:
      if resp.strip().strip("\n") == "":
        return {}, respCode
      print("Got non JSON response:")
      print(resp)
      print("-----------")
      self.assertTrue(False)

  def callKongServiceWithFiles(self, api, headers, method, files, expectedResponses):
    resp, respCode = testUtils.callServiceSendMultiPartFiles(self, self.kong_server + api, headers, method, 1, expectedResponses, files)
    try:
      return json.loads(resp), respCode
    except:
      if resp.strip().strip("\n") == "":
        return {}, respCode
      print("Got non JSON response:")
      print(resp)
      print("-----------")
      self.assertTrue(False)

  def deleteAllCerts(self):
    #used before tests that rely on certs data
    cmdToExecute = "./scripts/kong_delete_all_certs " + self.kong_server
    expectedOutput = ""

    expectedErrorOutput = None
    a = self.executeCommand(cmdToExecute, expectedOutput, expectedErrorOutput, [0], 1, True)

  #return False if it didn't have to delete because not there
  def deleteService(self, serviceName):
    #get service
    resp, respCode = self.callKongService("/services/" + serviceName, {}, "get", None, [200, 404])
    if respCode == 404:
      #service dosen't exist
      return False

    #get list of routes
    resp, respCode = self.callKongService("/services/" + serviceName + "/routes", {}, "get", None, [200])

    #delete all routes
    for x in resp["data"]:
      resp, respCode = self.callKongService("/routes/" + x["id"], {}, "delete", None, [204])

    #delete service
    resp, respCode = self.callKongService("/services/" + serviceName, {}, "delete", None, [204])

    #check service no longer getable
    resp, respCode = self.callKongService("/services/" + serviceName, {}, "get", None, [404])

  def createServiceAndRoute(self, serviceName, routeDICT):
    cmdToExecute = "./scripts/kong_install_service_and_route"
    cmdToExecute += " " + self.kong_server
    cmdToExecute += " " + serviceName
    cmdToExecute += " http"
    cmdToExecute += " www.host.com"
    cmdToExecute += " 80"
    cmdToExecute += " /"
    cmdToExecute += " " + routeDICT["protocol"]
    cmdToExecute += " " + routeDICT["host"]
    cmdToExecute += " " + routeDICT["path"]
    cmdToExecute += " GET"
    cmdToExecute += " null"
    cmdToExecute += " null"

    expectedOutput = ""
    expectedOutput += "Start of ./scripts/kong_install_service_and_route\n"
    expectedOutput += "Installing service for \n"
    expectedOutput += "Invalid paramaters expecting 12 but 0 were supplied\n"
    expectedErrorOutput = None

    a = self.executeCommand(cmdToExecute, expectedOutput, expectedErrorOutput, [0], 1, True)

    ret = {
        "serviceID": None,
        "routeID": None
    }
    for line in a.stdout.decode().split('\n'):
      if line.startswith(" - service id: "):
        ret["serviceID"] = line[15:]
      if line.startswith("CREATED_ROUTE_ID:"):
        ret["routeID"] = line[17:]

    return ret
