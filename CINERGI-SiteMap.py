
# coding: utf-8

# 

# In[9]:

from datetime import datetime
import requests
import sys
# see http://docs.python-requests.org/en/master/user/quickstart/ for package documentation


geoportalBaseURL = 'http://datadiscoverystudio.org/geoportal/'
catalogISOmetadataBase = geoportalBaseURL + 'rest/metadata/item/'

print catalogISOmetadataBase
XML_HEADER = '<?xml version="1.0" encoding="UTF-8"?>'

fileLocationBase = 'c:\\tmp\\'
print fileLocationBase

sitemaptohtml = 'https://raw.githubusercontent.com/CINERGI/xmlsitemap/master/xml-sitemap.xsl'
#suggest copying the xslt file into the same directory with the sitemaps, in which case, use this
# value for sitemaptohtml:
# sitemaptohtml = 'xml-sitemap.xsl'

# first some utility functions for file generation and writing
def writeLinks( response, mfile ):
#   writes entries in sitemap file, with URL for metadata record as html; the record
# is expected to include a schema.org JSON-LD script for use by the search indexers
    for hit in response["hits"]["hits"]:
#        hittitle = hit["_source"]["title"]
        try:
            hitid = hit["_id"]
            hitmodified =  hit["_source"]["sys_modified_dt"]
#        print "title: ", hittitle, " id: ", hitid, " date: ", hitmodified  

            mfile.write('<url>')
            mfile.write("\n")
# original CINERGI catalog location
#mfile.write('<loc>http://cinergi.sdsc.edu/geoportal/rest/metadata/item/' 
#                       + hitid + '/html</loc>')
            mfile.write('<loc>' + catalogISOmetadataBase + hitid + '/html</loc>')
            mfile.write("\n")
            mfile.write('<lastmod>' + hitmodified + '</lastmod>')
            mfile.write("\n")
            mfile.write('<changefreq>monthly</changefreq>')
            mfile.write("\n")
#        mfile.write('<priority>0.8</priority>')
#        mfile.write("\n")
            mfile.write('</url>')
            mfile.write("\n")
        except:
            print("ERROR writing sitemap url for _id= " + hitid)
            print(sys.exc_info()[1])
    return

def indexFile():
# set up the sitemap index. This file has a link to each sitemap file. 
# sitemaps are limited to 10000 entries, so if there is a bigger catalog, have
# to generate multiple sitemaps and point to them from the index.
    try:
        file_object  = open(fileLocationBase + "DDSSiteIndex.xml", "w")
    except:
        print("ERROR: Can't open the index file, bailing out")
        print(sys.exc_info()[1])
        sys.exit(0)
    # put in the header stuff
    file_object.write(XML_HEADER)
    file_object.write("\n")
    file_object.write('<?xml-stylesheet type="text/xsl" href="' + sitemaptohtml + '"?>')
    file_object.write('\n')
    file_object.write('<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    file_object.write("\n")

    return(file_object)

def siteMapFile(name):
# opens a new empty sitemap file and returns the file_object for writing to it.
    try:
        file_object  = open(fileLocationBase + name, "w")
    except:
        print("ERROR: Can't open the new sitemap file: " + name + ", bailing out")
        print(sys.exc_info()[1])
        sys.exit(0)
        
    #put in the header stuff
    file_object.write(XML_HEADER)
    file_object.write('\n')
    file_object.write('<?xml-stylesheet type="text/xsl" href="' + sitemaptohtml + '"?>')
    file_object.write('\n')
    file_object.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    file_object.write('\n')
    return(file_object)

# construct Elasticsearch URL with  search request
# espath="http://cinergi.sdsc.edu/geoportal/elastic/"
espath= geoportalBaseURL + "elastic/"
esindex="metadata"
esresource="/item/_search"
baseURL = espath+esindex+esresource
# need to use scrolling because there are >10000 records
# this is the time to live for the scroll index; renewed on each search call
p_scroll="1m"
#number of records to return in each batch. 
# This will be the number of links in each sitemap file
p_size="10000"
#use this for testing
#p_size="10"
# the only field we need for the sitemap is the modified date
# comma delimited list of index fields to return from the _source section of the hits object
#p_source="sys_modified_dt,title"
p_source="sys_modified_dt"

# first get the scroll index to start scrolling loop, and the total number of records

counter = 0
filecount = 0
#print counter

#first request to get scrolling set up
p = {'scroll':p_scroll, 
    'size' : p_size, 
    '_source' : p_source}
r = requests.get(baseURL, params=p)
print "request1: ", r.url

if r.status_code == requests.codes.ok:
    response = r.json()
    totalRecords = response["hits"]["total"]
    scrollID = response["_scroll_id"]

    #    set up the index file
    indexhandle = indexFile()
    print "total records: ", totalRecords
    sitemapfilename = "ddssitemap" + str(filecount)+ ".xml"
    sitemaphandle = siteMapFile(sitemapfilename)
    writeLinks(response, sitemaphandle)
    sitemaphandle.write('</urlset>')
    sitemaphandle.close() 
        
        #new index entry
    indexhandle.write('<sitemap>')
    indexhandle.write('\n')
#    indexhandle.write('<loc>http://cinergi.sdsc.edu/geoportal/' + sitemapfilename + '</loc>')
#  providing a full URL to put links in the sitemap index:
#    indexhandle.write('<loc>' + geoportalBaseURL + sitemapfilename + '</loc>')
# using local file paths also works, and is likely easier to maintain in the long run:
    indexhandle.write('<loc>' + sitemapfilename + '</loc>')
    indexhandle.write('\n')
    indexhandle.write('<lastmod>' + str(datetime.now())+ '</lastmod>')
    indexhandle.write('\n')
    indexhandle.write('</sitemap>')
    indexhandle.write('\n')
        
    filecount = filecount + 1
    counter = counter + int(p_size)
else:
    r.raise_for_status()
    sys.exit(0)
            
        
while counter < totalRecords:
# use this for testing:
#while counter < 50:
    #have to hit the scroll resource for Elasticsearch
    esresource="_search/scroll"
    #Geoportal Elasticsearch pass through requires publisher role to run the scroll resource
    espath="http://admin:admin@datadiscoverystudio.org/geoportal/elastic/"
    baseURL = espath+esresource
    p = { 'scroll':p_scroll, 
    'scroll_id' : scrollID}
    r = requests.get(baseURL, params=p)
#    print "request: ", r.url, r.status_code
#        print "raw response2: ", r, " status: ", r.status_code
#        print r.headers['content-type']
    if r.status_code == requests.codes.ok:
        response = r.json()
        scrollID = response["_scroll_id"]
        sitemapfilename = "ddssitemap" + str(filecount)+ ".xml"
        sitemaphandle = siteMapFile(sitemapfilename)
        writeLinks(response, sitemaphandle)
        sitemaphandle.write('</urlset>')
        sitemaphandle.close() 
        
        #new index entry
        indexhandle.write('<sitemap>')
        indexhandle.write('\n')
        indexhandle.write('<loc>' + geoportalBaseURL + sitemapfilename + '</loc>')
        indexhandle.write('\n')
        indexhandle.write('<lastmod>' + str(datetime.now())+ '</lastmod>')
        indexhandle.write('\n')
        indexhandle.write('</sitemap>')
        indexhandle.write('\n')
        
        filecount = filecount + 1
        counter = counter + int(p_size)
        print "count: ", counter
    else:
        r.raise_for_status()
        break

indexhandle.write('</sitemapindex>')        
indexhandle.close()
       
print "done, counter = ",counter


# In[ ]:




# In[ ]:



