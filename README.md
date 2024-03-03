# Book Review System

### Description
<p>A book review website. Users will be able to register in the website and then log in using their username and password.</p>
<p>Once they log in, they will be able to search for books, leave reviews for individual books, and see the reviews made by other people.</p>
<p>Finally, users will be able to query for book details and book reviews programmatically via the website’s API and will get a json response.</p>

### Database Used
<p>The project uses Microsoft Azure SQL.</p>

### Project Backbone
<p>The foundation of the project lies in the Python Flask Framework, complemented by fundamental HTML/CSS and JavaScript for frontend development.</p>



## To run this project
<ul>
<li>Clone the repository from GitHub to your local machine.</li>
<li>Create a virtual  environment using Python's built-in venv module. Activate it by running <code>source venv/bin/activate</code>.</li>
<li>Install all the dependencies using <code>pip3 install -r requirements.txt</code>.</li>
<li>Download the ODBC driver for SQL server into your laptop from <code>https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server?view=sql-server-ver16
</code></li>
<li>Set up a Azure SQL Database and add the values for the variable in the <code>config.py</code> file.</li>
</ul>

### Now that the Database is set

Run the following command:
```bash
python3 run.py
```

<hr>

