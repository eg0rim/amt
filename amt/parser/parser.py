# -*- coding: utf-8 -*-
# amt/parser/parser.py

# Copyright (c) 2024 Egor Im
# This file is part of Article Management Tool.
# Article Management Tool is free software: you can redistribute it and/or 
# modify it under the terms of the GNU General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Article Management Tool is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

from bs4 import BeautifulSoup
import urllib.request
import logging

def parseArxiv(arxivId: str)->dict:
    """parse arxive page of a paper
    
    :param str arxivId: arxiv id of the paper
    :return: dict of parsed data
    :rtype: dict
    """
    url = "http://export.arxiv.org/api/query?id_list=" + arxivId
    print(url)
    try:
        response = urllib.request.urlopen(url)
    except urllib.error.HTTPError:
        logging.error(msg="url not found")
        return None
    xml = response.read()
    soup = BeautifulSoup(xml, 'lxml')
    entry = soup.find("entry")
    data={}
    try: 
        data["link"] = entry.find("id").text
    except AttributeError:
        logging.error(msg="could not parse the page")
        return None
    data["arxiv_id"] = arxivId
    data["title"] = entry.find("title").text
    ver = data["link"].split("/")[-1].split('v')[-1]
    if ver:
        data["version"] = ver
    else:
        data["version"] = str(1)
    data["date_published"] = entry.find("published").text
    data["date_updated"] = entry.find("updated").text 
    data["summary"] = entry.find("summary").text 
    data["authors"] = [a.text[1:-1] for a in entry.find_all("author")]
    data["link_pdf"] = entry.find(title = "pdf")['href'] 
    data["p_category"] = entry.find("arxiv:primary_category")['term']  
    data["categories"] = [cat['term'] for cat in entry.find_all("category")]  
    try:
        data["comment"] = entry.find("arxiv:comment").text  
    except AttributeError:
        logging.error(msg="no comments found")
        pass
    try:
        data["doi"] = entry.find("arxiv:doi").text 
        data["journal"] = entry.find("arxiv:journal_ref").text 
    except AttributeError:
        logging.error(msg="no journal")
        pass
    return data
