import openai


openai.api_key = "your-openai-api-key"


def generate_article_outline(title, notes, tags, temperature=0.7):
    """
    Generates a detailed outline for an article based on provided title, notes, and tags.

    Parameters:
    title (str): The title of the article.
    notes (str): Notes or key points to be included in the article.
    tags (str): Comma-separated tags relevant to the article.
    temperature (float): Controls the creativity of the output. Default is 0.7.

    Returns:
    str: The generated outline of the article.
    """
    try:
        # Convert comma-separated tags into a string with each tag properly stripped and separated
        tag_string = ", ".join([tag.strip() for tag in tags.split(",")])

        # Form the prompt to be sent to OpenAI's model
        prompt = f"Title: {title}\nTags: {tag_string}\nNotes: {notes}\n\nCreate a detailed outline for an article based on the above information:"

        # Call the OpenAI API to generate the outline
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=200,  # Adjust max_tokens as needed for the outline
            temperature=temperature,
        )

        # Return the text portion of the response, stripped of any leading/trailing whitespace
        return response.choices[0].text.strip()
    except Exception as e:
        # Return the exception message in case of failure
        return str(e)


def generate_full_article_from_outline(outline, temperature=0.7):
    """
    Generates a full article based on a given outline.

    Parameters:
    outline (str): The outline of the article.
    temperature (float): Controls the creativity of the output. Default is 0.7.

    Returns:
    str: The generated full text of the article.
    """
    try:
        # Form the prompt to be sent to OpenAI's model using the provided outline
        prompt = (
            f"Write a detailed article based on the following outline:\n{outline}\n"
        )

        # Call the OpenAI API to generate the full article
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=800,  # Adjust max_tokens as needed for the full article
            temperature=temperature,
        )

        # Return the text portion of the response, stripped of any leading/trailing whitespace
        return response.choices[0].text.strip()
    except Exception as e:
        # Return the exception message in case of failure
        return str(e)
