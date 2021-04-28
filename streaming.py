import requests
import os
import time
import json
import configparser

from google.cloud import pubsub_v1
from google.api_core.exceptions import AlreadyExists, InvalidArgument


#
# Set the environment variable with your bearer_token
#
bearer_token = os.environ.get("BEARER_TOKEN")

#
# Setting up GCP Variables
#
project_id = "pnal28a21"
topic_id = "twitter28a"
topic_name = "projects/{project}/topics/{topic}".format(
    project=project_id,
    topic=topic_id,
)


def init_GCP():
    publisher_client = pubsub_v1.PublisherClient()
    # Check if the topic exists. If dont, the topic is created
    try:
        topic = publisher_client.create_topic(request={"name": topic_name})
    except AlreadyExists:
        return publisher_client
    except InvalidArgument:
        print(
            "Error: Please, check if the Project name '{project}' is correct and the topic name '{topic}' format is correct".format(
                project=project_id,
                topic=topic_id,
            )
        )
        return None


def get_header():
    header = {"Authorization": "Bearer {}".format(bearer_token)}
    return header


#
# Rules to filter the tweets to stream
#
def set_rules():
    header = get_header()
    rules = [
        {"value": "#ParoNacional #28Abril", "tag": "Paro Nal 28 Abril"},
        {"value": "#ParoNacional28A", "tag": "Paro Nal 28 Abril"},
        {"value": "#ReformaTributaria", "tag": "Reforma tributaria"},
        {"value": "#NoALaReformaTributaria", "tag": "Reforma tributaria"},
        {"value": "#NoALaReforma", "tag": "Reforma tributaria"},
        {
            "value": "#ParoNacional 28 abril (vandalos OR vandalismo)",
            "tag": "Paro Nal 21 Abril vandalismo",
        },
        {"value": "#ParoNacional 28 abril", "tag": "Paro Nal 28 Abril"},
        {
            "value": "#ParoNacional reforma tributaria",
            "tag": "Paro Nal reforma tributaria",
        },
        {
            "value": "#ParoNacional (Carrasquilla OR Duque)",
            "tag": "Paro Nal Carrasquilla Duque",
        },
        {"value": "#ParoNacional #AbusoPolicial", "tag": "Paro Nal Abuso Policial"},
        {
            "value": "(#ESMAD OR ESMAD) (gases OR disparos OR dispara OR disparan OR golpes OR golpea OR ilegal OR ilegalmente)",
            "tag": "Abuso policial",
        },
        {"value": "#ParoNacional Colombia", "tag": "Paro Nal Colombia"},
    ]
    payload = {"add": rules}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=header,
        json=payload,
    )

    if response.status_code != 201:
        raise Exception(
            "Cannot add rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    print("### Rules setting result")
    print(json.dumps(response.json()))
    print("###")


#
# Obtain all the current rules and delete them.
#
def delete_rules():
    header = get_header()
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream/rules", headers=header
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot get rules (HTTP {}): {}".format(response.status_code, response.text)
        )
    rules = response.json()

    if rules is None or "data" not in rules:
        return None

    ids = list(map(lambda rule: rule["id"], rules["data"]))
    payload = {"delete": {"ids": ids}}
    response = requests.post(
        "https://api.twitter.com/2/tweets/search/stream/rules",
        headers=header,
        json=payload,
    )
    if response.status_code != 200:
        raise Exception(
            "Cannot delete rules (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    print("### Rules deletion result")
    print(json.dumps(response.json()))
    print("###")


#
# Tweets sreaming
#
def get_tweets(set, publisher_client):
    header = get_header()
    response = requests.get(
        "https://api.twitter.com/2/tweets/search/stream",
        headers=header,
        stream=True,
    )

    if response.status_code != 200:
        raise Exception(
            "Cannot get stream (HTTP {}): {}".format(
                response.status_code, response.text
            )
        )
    for response_line in response.iter_lines():
        if response_line:
            json_response = json.loads(response_line)
            data = json.dumps(json_response).encode("utf-8")
            future = publisher_client.publish(topic_name, data)


def main():
    publisher_client = init_GCP()
    delete_rules()
    rules = set_rules()
    get_tweets(rules, publisher_client)


if __name__ == "__main__":
    main()
