from bs4 import BeautifulSoup
import requests
import sqlite3


def RepresentsInt(s):
	"""Checks if the given string represents an integer.
	Args:
		s: str
	Returns:
		boolean.
	"""
	try: 
		int(s)
		return True
	except ValueError:
		return False


def get_population(city):
	"""Returns the population of a given city.

	Args:
		city: link to wikipedia page of the city.
	"""
	website_url = requests.get(city).text
	soup = BeautifulSoup(website_url, 'lxml')
	city_table = soup.find('table', {'class':'infobox geography vcard'})
	if city_table is None:
		city_table = soup.find('table', {'class':'infobox vcard'}) # melbourne
	all_rows = city_table.findAll('tr')

	population = 0
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
						population =max(int(pop), population)

	return population


def extract_museum_char(wikipedia_link):
	"""Extracts the characteristics of the museum.
	Args:
		wikipedia_link: str, wikipedia link to the museum.
	Returns:
		dictionary containing following keys: Established, Website
	"""
	website_url = requests.get(wikipedia_link).text
	soup = BeautifulSoup(website_url, 'lxml')

	museum_info = soup.find('table', {'class':'infobox vcard'}) 
	if museum_info is not None:
		all_rows = museum_info.findAll('tr')
	else:
		all_rows = None

	details = {}
	details["Established"] = ""
	details["Website"] = ""

	if all_rows is not None:
		for row in all_rows:
			header = row.find('th')
			if header is not None:
				header = header.text.strip()
				if header == "Established" or header == "Website":
					content = row.find('td')
					if content is not None:
						details[header] = content.text

	return details


def extract_museum_list():
	"""Returns the table of museums as a dict."""

	website_url = requests.get('https://en.wikipedia.org/wiki/List_of_most_visited_museums').text
	soup = BeautifulSoup(website_url, 'lxml')

	museum_table = soup.find('table', {'class':'wikitable sortable'})
	all_rows = museum_table.findAll('tr')

	# ignore all_rows[0], all_rows[1]

	table = {}

	table["Museum Name"] = list()
	table["city"] = list()
	table["visitors"] = list()
	table["year"] = list()
	table["Population"] = list()
	table["Established"] = list()
	table["Website"] = list()

	museum_names = {}  # maintain the list to avoid double entries 

	for i in range(2, len(all_rows)):
		content = all_rows[i].findAll('td')
		if content[0].text not in museum_names:
			museum_names[content[0].text] = 1
			for j in range(0, len(content)):
				
				if j == 0: # to extract museum characteristics
					print(content[j].text)
					table["Museum Name"].append(content[j].text)
					link = content[j].findAll('a')[-1]
					details = extract_museum_char("https://en.wikipedia.org/" + link['href'])
					table["Established"].append(details["Established"])
					table["Website"].append(details["Website"])
				elif j == 1:
					table["city"].append(content[j].text)
					link = content[j].findAll('a')[-1]
					population = get_population("https://en.wikipedia.org/" + link['href'])
					table["Population"].append(population)
				elif j == 2:
					table["visitors"].append(content[j].text)
				elif j == 3:
					table["year"].append(content[j].text)

	# converting visitors per year into int.
	for i in range(len(table["visitors"])):
		table["visitors"][i] = int(table["visitors"][i].replace(",",""))

	# removing the extra references from the years 
	for i in range(len(table["year"])):
		table["year"][i] = int(table["year"][i].split("[")[0])

	return table


def create_sql_table(table):
	"""Creates a SQL table for the given dict table."""    

	connection = sqlite3.connect("museum_list.db") 
	crsr = connection.cursor()
	sql_command = """CREATE TABLE museum (  
					musueum_name VARCHAR(50) PRIMARY KEY,  
					city VARCHAR(30),  
					visitors INTEGER,  
					year INTEGER,
					population INTEGER,
					established VARCHAR(200),
					website VARCHAR(200));"""

	crsr.execute(sql_command)

	for i in range(len(table["Museum Name"])):
		sql_command = """INSERT INTO museum VALUES("{}", "{}", {}, {}, {}, "{}", "{}")""".format(table["Museum Name"][i],
			table["city"][i], table["visitors"][i], table["year"][i], 
			table["Population"][i], table["Established"][i], table["Website"][i])
		crsr.execute(sql_command)

	connection.commit() 
	connection.close() 


table = extract_museum_list()
create_sql_table(table)

