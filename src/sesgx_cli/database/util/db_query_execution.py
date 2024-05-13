from sqlalchemy import text
from sqlalchemy.orm import Session


class ReviewDoesNotExist(Exception):
    """The review passed as a param does not exist in the database."""


def get_results_from_db(
    queries: dict[str, str],
    session: Session,
) -> dict[str, dict]:
    """
    Responsible for retrieving all the data needed to construct a results Excel file.

    Args:
        queries: all the queries necessary to compose the final Excel file.
        check_review_query: query to ensure the SLR exists.
        session: A db session.

    Returns: a dictionary with the following structure:
        {'{query_name}': {'columns': all the columns that were in the select statement
                        'data': all the Rows resulting of the query}}

    """
    results: dict = {}

    for query_name, query in queries.items():
        cursor = session.execute(text(query))
        exec_results = cursor.fetchall()
        results[query_name] = {
            "columns": tuple(cursor.keys()),
            "data": exec_results,
        }

    return results


def get_strategies_used(
    queries: dict[str, str],
    check_review_query: str,
    session: Session,
) -> dict[str, dict]:
    """Retrieves the strategies used in the review.

    Args:
        queries: sql queries to be executed.
        check_review_query: query to check if the review exists.
        session: database connection session.
    Raises:
        ReviewDoesNotExist: If the review does not exist in the database.
    Returns:
        Query results in a dictionary.
    """
    results: dict = {}

    if not bool(session.execute(text(check_review_query)).scalar()):
        raise ReviewDoesNotExist()

    for query_name, query in queries.items():
        cursor = session.execute(text(query))
        exec_results = cursor.fetchall()
        results[query_name] = [i[0] for i in exec_results]

    return results
