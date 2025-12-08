import mysql.connector

class DatabaseConnector:
    def __init__(self, host, user, password, database):
        """
        Initialize a DatabaseConnector instance with connection credentials.

        Parameters:
            host (str): The database server hostname or IP address.
            user (str): The username used to authenticate with the database.
            password (str): The password used to authenticate with the database.
            database (str): The name of the database to connect to.

        Attributes:
            host (str): Stored hostname/IP for the database server.
            user (str): Stored username for database authentication.
            password (str): Stored password for database authentication.
            database (str): Stored target database name.
            connection (Optional[Any]): Database connection handle; initialized to None until connected.
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

    def connect(self):
        """
        Establish a connection to the configured MySQL database using the instance's
        host, user, password, and database attributes.

        On success, sets `self.connection` to an active `mysql.connector.MySQLConnection`
        and prints "Connection successful." On failure, catches `mysql.connector.Error`,
        prints the error message, and sets `self.connection` to `None`.

        Returns:
            None
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Connection successful.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")
            self.connection = None

    def close(self):
        """
        Close the active database connection.

        This method checks whether a database connection exists and, if so, closes it
        to release associated resources. After closing, it prints a confirmation message
        indicating that the connection has been closed.

        Note:
        - Safe to call multiple times; if no connection exists, no action is taken.

        Raises:
        - Any exceptions propagated by the underlying connection's close implementation.

        Returns:
        - None
        """
        if self.connection:
            self.connection.close()
            print("Connection closed.")

    def execute_query(self, query, params=None):
        """
        Execute a SQL query using the active MySQL connection.

        This method ensures a connection is available, executes the given query with optional
        parameters, and handles result retrieval and transaction commits based on the query type.
        For SELECT queries, it returns a list of rows as dictionaries. For non-SELECT queries,
        it commits the transaction and returns the number of affected rows. On error, it logs
        the exception and returns None. The cursor is always closed before exiting.

        Parameters:
            query (str): The SQL query to execute. Supports both SELECT and non-SELECT statements.
            params (tuple | dict | None): Optional parameters to bind to the query.

        Returns:
            list[dict] | int | None:
                - list[dict]: Result set for SELECT queries (each row as a dictionary).
                - int: Number of rows affected for non-SELECT queries.
                - None: If an error occurs during query execution.

        Raises:
            None explicitly. Errors are caught, logged, and result in a None return value.
        """
        if not self.connection:
            self.connect()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(query, params)
            if query.strip().lower().startswith("select"):
                result = cursor.fetchall()
                return result
            else:
                self.connection.commit()
                return cursor.rowcount
        except mysql.connector.Error as err:
            print(f"Query error: {err}")
            return None
        finally:
            cursor.close()