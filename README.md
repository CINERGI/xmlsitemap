# xmlsitemap
tools for generating xml sitemap for CINERGI catalog; linked URLs will show html versions of ISO metadata records with schema.org Dataset markup included as a script.

CINERGI-SiteMap.ipynb  Code is implemented in iPython notebook to start. 

xml-sitemap.xsl  XML transform to display sitemap or sitemap index as html. Include as stylesheet directive in sitemap xml file head. The xsl needs to be in the same server directory from which the site maps are accessed

ISO19139ToSchemaOrgDataset.xslt  see https://github.com/usgin/metadataTransforms/iso-19139-to-HTMLwSDO for current version of transform to generate html with schema.org script for commercial search engines.