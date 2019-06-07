#!/usr/bin/python3
import easygui
import untangle
import os
import sys
from shutil import copyfile
from time import gmtime, strftime
from re import sub
from decimal import Decimal

#/ Configurations
d_path = 'PATH_TO_FTP_SERVER'
save_path = 'YOUR_SAVE_PATH'

#/Get XML invoice
invoice_file = easygui.fileopenbox(msg="Select File", title="Select File",default=d_path+"*.xml", multiple=False)
if invoice_file == None:
    sys.exit()
script_path = os.path.dirname(os.path.realpath(__file__))

#/Save file
date = strftime("%Y%m%d", gmtime())
alreadyExists = os.path.isfile(save_path+date+"_library_invoice.csv")
if alreadyExists == True:
    fh = open(save_path+date+"_library_invoice_a.csv", "a")
else:
    fh = open(save_path+date+"_library_invoice.csv", "a")

#/Parse XML
doc = untangle.parse(invoice_file)
xml = doc.payment_data.invoice_list.invoice
for inv in xml:
    #/Invoice ID
    Invoice_ID               = inv.invoice_number.cdata
    if "UT_RT" in Invoice_ID: continue #/Skips Use Tax invoices
    
    #/Other values
    Invoice_Dt               = inv.invoice_date.cdata
    vendor_FinancialSys_Code = inv.vendor_FinancialSys_Code.cdata
    Vendor_Id                = vendor_FinancialSys_Code[:10]
    dt                       = inv.invoice_ownered_entity.creationDate.cdata
    Acctg_Dt                 = dt[4:6]+"/"+dt[6:8]+"/"+dt[0:4]
    Vchr_Line                = '1'       #/Static value
    GL_Unit                  = 'SLCMP'   #/Static value
    Descr                    = 'REGULAR' #/Static value
    
    #/Gross Amount
    Gross_Amt                = inv.invoice_amount.sum.cdata
    Gross_Amt                = Decimal(sub(r'[^-\d.]', '', Gross_Amt)) #/includes credit amounts
    
    #/Skip invoices over $2,500
    if Gross_Amt > 2500: continue
    
    #/Sales Tax
    Sales_Tax                = inv.vat_info.vat_amount.cdata
    Sales_Tax                = Decimal(sub(r'[^-\d.]', '', Sales_Tax)) #/includes credit amounts
    
    #/SUT - Must be 'S', 'E', or 'U'
    if Sales_Tax != "": SUT = 'S'
    if Sales_Tax == 0.0: SUT = 'E'
    if "/UT" in Invoice_ID: SUT = 'U'
    
    #/Ship_To_Location - Must be '0820' or 'NO TAX'
    if Sales_Tax == 0.0: Ship_To_Location = 'NOTAX'
    if Sales_Tax != 0.0 or SUT == 'U': Ship_To_Location = '0820'
    
    #/Overhead (if any)
    overhead                 = inv.additional_charges.overhead_amount.cdata
    
    #/Freight Amount
    Freight_Amt              = inv.additional_charges.shipment_amount.cdata
    
    if Freight_Amt == '0.0':
        Freight_Amt = overhead
    Freight_Amt              = Decimal(sub(r'[^-\d.]', '', Freight_Amt)) #/includes credit amounts
    
    #/Merchandise Amount (Net Amount)
    Merchandise_Amt          = Gross_Amt - Freight_Amt - Sales_Tax
    
    #/Address Sequence
    Addr_Seq                 = vendor_FinancialSys_Code[11:]
    
    #/Blank out zero fields
    if Sales_Tax   == 0.0: Sales_Tax = ""
    if Freight_Amt == 0.0: Freight_Amt = ""
    
    #/External_id #############################################################
    lines = inv.invoice_line_list.invoice_line
    for line in lines:
        line_number = int(line.line_number.cdata)
        if line_number < 999991:
            fund_line = line.fund_info_list.fund_info
            external_id = fund_line.external_id.cdata
            
            #/Split system code by spaces        
            ids = external_id.split()
            
            #/Check for blank indexes and fill
            l = len(ids)
            rest = 6 - l
            for i in range(rest):
                ids.append("")
                
            #/Grab values
            Account  = ids[0]
            Fund     = ids[1]
            Dept     = ids[2]
            Program  = ids[3]
            Class    = ids[4]
            Project  = ids[5]
    
    ###########################################################################
    
    #/Write output to CSV file
    invoice_line = f"{Invoice_ID},{Invoice_Dt},{Vendor_Id},{Acctg_Dt},{Vchr_Line},{GL_Unit},,,,{str(Gross_Amt)},{str(Merchandise_Amt)},{Descr},,{Account},{Fund},{Dept},{Program},{Class},,{Ship_To_Location},{SUT},{str(Sales_Tax)},{str(Freight_Amt)},,,,,,,{Addr_Seq},,,,,,,,,,"
    fh.write(f"{invoice_line}\n")
    
#/Finish
easygui.msgbox("Done.", title="Finished", )
fh.close