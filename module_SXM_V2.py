#!/usr/bin/env python
# version 2.0 jmb (11/03/2015)


import struct,binascii
import os,sys
import argparse
import codecs

######## constants ################################
debug=0
sxm_extension="sxm"
###################################################

def num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

###################################################
#Definition des conteneurs
#filenames=()
#channel=()



###################################################
if __name__ == '__main__':

 parser = argparse.ArgumentParser()
 group = parser.add_mutually_exclusive_group()
 #parser.add_argument("-d", "--debug", help="output some informations for debugging", action="store_true")
 group.add_argument("-d", "--debug", help="increase output for debugging", type=int, choices=[1,2])
 group.add_argument("-o", "--output", help="write output in file",action="store_true")
 parser.add_argument("-f",dest="filenames", help="filename(s) with sxm extension (* accepted)", nargs='+',required=True)
 parser.add_argument("-v", "--verbosity", help="increase output verbosity", action="count", default=0)
 parser.add_argument("-c",dest="channel" , help="list of channels to be extracted", nargs='+',required=True)
 args = parser.parse_args()
 filenames = args.filenames
 channel=args.channel
 debug = args.debug
# print "Channel a extraire:",channel
 index_channel=[0]*len(channel)
# print index_channel
# for i in index_channel:
#	print i
# print "Fichier a traiter:",filenames
 
################################
# try to find the index of data
 for filename in filenames:

   if os.path.isdir(filename):
      if args.verbosity > 1:
          print "Info : %s is dir..." % filename
      continue

   fileOutput = os.path.splitext(filename)[0]+".txt"
   fileExtension = os.path.splitext(filename)[1][1:]
   if fileExtension != sxm_extension and fileExtension != "" :
      if args.verbosity > 1:
           print "Info : %s has bad extension : no processed..." % filename
      continue
 
   with open(filename, "r") as fp:
     while True:
      line = fp.readline()

      if ":SCAN_PIXELS:" in line:
        tmp = fp.readline()
        a,b = tmp.split()
        Nbr_pixels = num(a)
        Nbr_lines = num(b)
        Nbr_data = Nbr_pixels * Nbr_lines
        Data_size = Nbr_data * 4  # float = 4 bytes
        if args.verbosity > 0:
            print "\nfilename : %s" % filename
            print "  Nbr_pixels Nbr_lines Nbr_data Data_size"
            print "    %d        %d       %d     %d" % (Nbr_pixels,Nbr_lines,Nbr_data,Data_size)
            print "output file : %s" % fileOutput

      if ":DATA_INFO:" in line:
        # read colunm headers : Channel Name Unit Direction Calibration Offset
        fp.readline()
        data_index=0
        while True:
          line = fp.readline() 
	  e=0
	  for i_channel in channel:
		if i_channel in line:
			index_channel[e]=data_index
		e=e+1
          if ":SCANIT_END:" in line:   ########## condition exit ###########
            break
          data_index+=1
        if debug:
          print "I data index : %d" % data_index
      
      if ":SCAN_RANGE:" in line:
        # read 2 floats	
        tmp = fp.readline()
        a,b = tmp.split()
        #print tmp, a, b
        x_ampl = 1.0e+09 * num(a)  # in nm
        y_ampl = 1.0e+09 * num(b)  # in nm
        z_ampl = 0  # TODO : how to computer this kOhm ( max of kOhm ? )

      if ":SCANIT_END:" in line:
        break

###################
# found the header size ( diff between line and matrix ! )
   with open(filename, "rb") as fb:
     while True:
       if ord(fb.read(1)) == 26:
         if ord(fb.read(1)) == 4:
            Header_size = fb.tell()
            break
   if debug >= 1:
        print "Header_size : %d bytes" % Header_size
 #sys.exit()
 
###################
# read binary data
# originale   
#  Seek_offset = int(Header_size + ( data_index*Data_size*2 ) + Data_size)
indice_mat=-1
for index in index_channel:
   indice_mat=indice_mat+1
   Seek_offset = int(Header_size + ( index*Data_size*2 ))
   if debug >= 1:
     print "Seek offset : %d bytes \n" % Seek_offset

   with open(filename, "rb") as fb:
     fb.seek(Seek_offset)

     kOhms=[[0 for x in range(Nbr_pixels)] for x in range(Nbr_lines)] 
     kOhms_tmp=[[0 for x in range(Nbr_pixels)] for x in range(Nbr_lines)] 
     for i in range(0, Nbr_lines):
       for j in range(0, Nbr_pixels): 
         a = fb.read(4)
         #print binascii.hexlify(a)
         (tmp,) =  struct.unpack('>f'.encode("ascii"), a)
         kOhms_tmp[i][j] = tmp
     # re-order the matrix
     for i in range(0, Nbr_lines):
       for j in range(0, Nbr_pixels):
         kOhms[i][j]=kOhms_tmp[Nbr_lines-1-i][Nbr_pixels-1-j]
         

   #if args.output :
   if True :
     file = codecs.open(fileOutput.replace(".txt","")+"_"+str(channel[indice_mat]).replace(" ","_")+".txt", "w", "utf-8")

#     file.write("WSxM file copyright Nanotec Electronica\n")
#     file.write("WSxM ASCII Matrix file\n")
#     if x_ampl > 1000:
#       file.write(u"X Amplitude: %d \u00B5m\n" % int(x_ampl/1.0e+3) )
#     else:
#       file.write("X Amplitude: %d nm\n" % x_ampl)
#     if y_ampl > 1000:
#       file.write(u"Y Amplitude: %d \u00B5m\n" % int(y_ampl/1.0e+3) )
#     else:
#       file.write("Y Amplitude: %d nm\n" % y_ampl)
#
#     z_ampl=0.0
#     for i in range(0, Nbr_lines):
#       tmp=max(kOhms[i])
#       if tmp > z_ampl:
#         z_ampl = tmp
#        
#     file.write("Z Amplitude: %.3f KOhm\n" % z_ampl)

     for i in range(0, Nbr_lines):
        file.write('%.12f '*Nbr_pixels % tuple(kOhms[i]))
        file.write("\n")
     file.close()
     #sys.exit()
