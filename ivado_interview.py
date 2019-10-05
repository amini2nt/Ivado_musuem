import requests
from bs4 import BeautifulSoup
import ipdb



def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False

def get_population(country):

	website_url = requests.get(country).text
	soup = BeautifulSoup(website_url, 'lxml')
	city_table = soup.find('table', {'class':'infobox geography vcard'})
	if city_table is None:
		city_table = soup.find('table', {'class':'infobox vcard'}) #melbourne
	all_rows = city_table.findAll('tr')

	pops = 0
	start = False
	for row in all_rows:
		if "Population" in row.text:
			start=True
		if start==True:
			pop = row.find('td')
			if pop is not None:
				pop = pop.text
				pop = pop.split("[")[0] #vatican
				if "," in pop:
					pop = pop.split("(")[0] #melbourne
					pop = pop.replace(",","")
					if RepresentsInt(pop):
						pops =max(int(pop), pops)

	return pops


#print(get_population("https://en.wikipedia.org/wiki/Melbourne"))

def extract_museum_list():

	website_url = requests.get('https://en.wikipedia.org/wiki/List_of_most_visited_museums').text
	soup = BeautifulSoup(website_url, 'lxml')
	musuem_table = soup.find('table', {'class':'wikitable sortable'})
	all_rows = musuem_table.findAll('tr')

	# ignore all_rows[0]
	heading = all_rows[1].findAll('th')

	heading_list = []

	for head in heading:
		heading_list.append(head.text)

	heading_list.append("Population")

	table = []
	for heading in heading_list:
		table.append(list())

	mnames = {}	

	for i in range(2, len(all_rows)):
		#ipdb.set_trace()
		content = all_rows[i].findAll('td')
		if content[0].text not in mnames:
			mnames[content[0].text] = 1
			for j in range(0, len(content)):

				table[j].append(content[j].text)
				if j == 1:
					print(content[j].text)
					link = content[j].findAll('a')[-1]
					popsize = get_population("https://en.wikipedia.org/" + link['href'])
					print(popsize)
					table[-1].append(popsize)

	# converting visitors per year into int.
	for i in range(len(table[2])):
		table[2][i] = int(table[2][i].replace(",",""))

	# removing the extra references from the years 
	for i in range(len(table[3])):
		table[3][i] = int(table[3][i].split("[")[0])

	return heading_list, table

def create_sql_table(table):	

	connection = sqlite3.connect("myTable.db") 
	crsr = connection.cursor()
	sql_command = """CREATE TABLE musuem (  
					musueum_name VARCHAR(50) PRIMARY KEY,  
					city VARCHAR(30),  
					visitors INTEGER,  
					year INTEGER,
					population INTEGER);"""

	crsr.execute(sql_command)

	for i in range(len(table[0])):
		sql_command = """INSERT INTO musuem VALUES("{}", "{}", {}, {}, {})""".format(table[0][i], table[1][i], table[2][i], table[3][i], table[4][i])
		crsr.execute(sql_command)

	connection.commit() 
	connection.close() 


heading_list, table = extract_museum_list()
create_sql_table(table)

