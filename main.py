import acipdt
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import sys
import xlrd
import xlwt
from xlutils.copy import copy
import time
from orderedset import OrderedSet


# Function to load the configuration workbook, uses xlrd
def read_in():
    try:
        wb = xlrd.open_workbook('ACI Deploy.xls')
        print("Workbook Loaded.")
    except Exception, e:
        print("Something went wrong logging opening the workbook - ABORT!")
        sys.exit(e)
    return wb


# Function to find all keywords (keys) in the workbook
def findKeys(ws, rows):
    func_list = OrderedSet()
    for i in range(2, rows):
        if (ws.cell(i, 0)).value:
            func_list.add((ws.cell(i, 0)).value)
        else:
            i += 1
    return func_list


# Function to count how many iterations of a key exists in workbook
def countKeys(ws, rows, func):
    count = 0
    for i in range(2, rows):
        if (ws.cell(i, 0)).value == func:
            count += 1
        else:
            i += 1
    return count


# Function to find the variable names in the workbook and load them
# into a dictionary w/ the values as the variables. This creates a nested
# dictionary that is count parent entries long
def findVars(ws, rows, func, count):
    var_list = []
    var_dict = {}
    for i in range(2, rows):
        if (ws.cell(i, 0)).value == func:
            try:
                for x in range(4, 16):
                    if (ws.cell(i - 1, x)).value:
                        var_list.append((ws.cell(i - 1, x)).value)
                    else:
                        x += 1
            except:
                pass
            break
    while count > 0:
        var_dict[count] = {}
        var_count = 0
        for z in var_list:
            var_dict[count][z] = ws.cell(i + count - 1, 4 + var_count).value
            var_count += 1
        var_dict[count]['row'] = i + count - 1
        count -= 1
    return var_dict


def wb_update(wr_ws, status, i):
    # build green and red style sheets for excel
    green_st = xlwt.easyxf('pattern: pattern solid;')
    green_st.pattern.pattern_fore_colour = 3
    red_st = xlwt.easyxf('pattern: pattern solid;')
    red_st.pattern.pattern_fore_colour = 2
    yellow_st = xlwt.easyxf('pattern: pattern solid;')
    yellow_st.pattern.pattern_fore_colour = 5
    # if stanzas to catch the status code from the request
    # and then input the appropriate information in the workbook
    # this then writes the changes to the doc
    if status == 200:
        wr_ws.write(i, 1, 'Success (200)', green_st)
    if status == 400:
        print("Error 400 - Bad Request - ABORT!")
        print("Probably have a bad URL or payload")
        wr_ws.write(i, 1, 'Bad Request (400)', red_st)
        pass
    if status == 401:
        print("Error 401 - Unauthorized - ABORT!")
        print("Probably have incorrect credentials")
        wr_ws.write(i, 1, 'Unauthorized (401)', red_st)
        pass
    if status == 403:
        print("Error 403 - Forbidden - ABORT!")
        print("Server refuses to handle your request")
        wr_ws.write(i, 1, 'Forbidden (403)', red_st)
        pass
    if status == 404:
        print("Error 404 - Not Found - ABORT!")
        print("Seems like you're trying to POST to a page that doesn't"
              " exist.")
        wr_ws.write(i, 1, 'Not Found (400)', red_st)
        pass
    if status == 666:
        print("Error - Something failed!")
        print("The POST failed, see stdout for the exception.")
        wr_ws.write(i, 1, 'Unkown Failure', yellow_st)
        pass
    if status == 667:
        print("Error - Invalid Input!")
        print("Invalid integer or other input.")
        wr_ws.write(i, 1, 'Unkown Failure', yellow_st)
        pass


# Load the appropriate worksheet, get all the keys (functions) that need to be
# ran and load the variables, then call the method to build out fabric pod
# policies and device comissioning
def pod_policies(apic, cookies, wb, wr_wb):
    ws = wb.sheet_by_name('Fabric Pod Policies')
    wr_ws = wr_wb.get_sheet(0)
    rows = ws.nrows
    func_list = findKeys(ws, rows)
    podpol = acipdt.FabPodPol(apic, cookies)
    for func in func_list:
        count = countKeys(ws, rows, func)
        var_dict = findVars(ws, rows, func, count)
        for pos in var_dict:
            row_num = var_dict[pos]['row']
            del var_dict[pos]['row']
            status = eval("podpol.%s(**var_dict[pos])" % func)
            wb_update(wr_ws, status, row_num)
            time.sleep(.025)


# Load the appropriate worksheet, get all the keys (functions) that need to be
# ran and load the variables, then call the method to build out fabric access
# policies
def access_policies(apic, cookies, wb, wr_wb):
    ws = wb.sheet_by_name('Fabric Access Policies')
    wr_ws = wr_wb.get_sheet(1)
    rows = ws.nrows
    func_list = findKeys(ws, rows)
    accpol = acipdt.FabAccPol(apic, cookies)
    for func in func_list:
        count = countKeys(ws, rows, func)
        var_dict = findVars(ws, rows, func, count)
        for pos in var_dict:
            row_num = var_dict[pos]['row']
            del var_dict[pos]['row']
            status = eval("accpol.%s(**var_dict[pos])" % func)
            wb_update(wr_ws, status, row_num)
            time.sleep(.025)


# Load the appropriate worksheet, get all the keys (functions) that need to be
# ran and load the variables, then call the method to build out fabric pod
# policies and device comissioning
def tn_policies(apic, cookies, wb, wr_wb):
    ws = wb.sheet_by_name('Tenant Configuration')
    wr_ws = wr_wb.get_sheet(2)
    rows = ws.nrows
    func_list = findKeys(ws, rows)
    tnpol = acipdt.FabTnPol(apic, cookies)
    for func in func_list:
        count = countKeys(ws, rows, func)
        var_dict = findVars(ws, rows, func, count)
        for pos in var_dict:
            row_num = var_dict[pos]['row']
            del var_dict[pos]['row']
            status = eval("tnpol.%s(**var_dict[pos])" % func)
            wb_update(wr_ws, status, row_num)
            time.sleep(.025)


# Load the appropriate worksheet, get all the keys (functions) that need to be
# ran and load the variables, then call the method to build out l3 out
# policies and device comissioning
def l3_policies(apic, cookies, wb, wr_wb):
    ws = wb.sheet_by_name('L3 Out')
    wr_ws = wr_wb.get_sheet(3)
    rows = ws.nrows
    func_list = findKeys(ws, rows)
    l3pol = acipdt.FabL3Pol(apic, cookies)
    for func in func_list:
        count = countKeys(ws, rows, func)
        var_dict = findVars(ws, rows, func, count)
        for pos in var_dict:
            row_num = var_dict[pos]['row']
            del var_dict[pos]['row']
            status = eval("l3pol.%s(**var_dict[pos])" % func)
            wb_update(wr_ws, status, row_num)
            time.sleep(.025)


def main():
    # Disable urllib3 warnings
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    # Static APIC information
    apic = '10.10.10.20'
    user = 'admin'
    pword = 'password'
    # Initialize the fabric login method, passing appropriate variables
    fablogin = acipdt.FabLogin(apic, user, pword)
    # Run the login and load the cookies var
    cookies = fablogin.login()
    # Load workbook
    wb = read_in()
    # Copy workbook to a RW version
    wr_wb = copy(wb)
    # Run pod policies function, pass apic and cookies
    pod_policies(apic, cookies, wb, wr_wb)
    # Run access policies function, pass apic and cookies
    access_policies(apic, cookies, wb, wr_wb)
    # Run tenant policies function, pass apic and cookies
    tn_policies(apic, cookies, wb, wr_wb)
    # Run l3 policies function, pass apic and cookies
    l3_policies(apic, cookies, wb, wr_wb)
    # Write to the workbook
    wr_wb.save('ACI Deploy.xls')

if __name__ == '__main__':
    main()
