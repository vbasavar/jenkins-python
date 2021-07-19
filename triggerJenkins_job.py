import requests
import json
import re
import time
import argparse
import logging
logger = logging.getLogger("dbusercreation")
logger.setLevel(logging.DEBUG)

logs=logging.StreamHandler()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
logs.setFormatter(formatter)
logger.addHandler(logs)

args = argparse.ArgumentParser()

# These will be job parameters or if you dont want to pass any parameter you  can set buildWithParameters=False ( line no 30 )
args.add_argument("-i", "--abc", required=True)
args.add_argument("-d", "--def", required=True)
args.add_argument("-H", "--ghi", required=True)
args.add_argument("-T", "--jkl", required=True)
args = args.parse_args()

job_name = "<job_name>"
jenkins_url = "<jenkins_url>"
jenkins_user = "<jenkins_usr>"
jenkins_pwd = "<jenkins_token>"
# to get the jenkins token go to 
buildWithParameters = True
job_poll_interval = 20
job_poll_attempts = 1
QUEUE_POLL_INTERVAL = 5
queue_poll_attempts = 1
job_params = {'token': jenkins_pwd,
              'dbInstance': args.abc,
              'database': args.def,
              'ipaddress': args.ghi,
              'userid': args.jkl,
              }
auth = (jenkins_user, jenkins_pwd)


# Triggers jenkins job.
# buildWithParameters ignore this parameter if you wish you dont want to pass any parameters to the jenkins job.
def trigger_jenkins_job(jenkins_url, job_name, job_params, auth):
    response = requests.post(jenkins_url + "/job/" + job_name + "/buildWithParameters?", auth=auth, params=job_params,
                             verify=False)
    queue = re.match(r"http.+(queue.+)\/", response.headers['Location'])
    queue_id = queue.group(1)
    job_info_url = '{}/{}/api/json?pretty=true'.format(jenkins_url, queue_id)
    return job_info_url

# This will fetch the job info
def get_jenkins_job_info(job_info_url):
    global queue_poll_attempts
    while queue_poll_attempts < 5:
        logger.info(f"job_info_url : {job_info_url}")

        stats = requests.post(job_info_url, auth=auth, verify=False)
        try:
            job_url = stats.json()['executable']['url']
            return job_url
            break
        except:
            logger.info("{}: Status: Job not yet started after {} attempts".format(time.ctime(), queue_poll_attempts))
            time.sleep(QUEUE_POLL_INTERVAL)
            queue_poll_attempts = queue_poll_attempts + 1

# This wil parse the job output console and also the job status
def get_jenkins_job_build(job_url):
    global job_poll_attempts
    while job_poll_attempts < 181:
        logger.info("{}: Job started and URL: {}".format(time.ctime(), job_url))
        logger.info(f"job_url : {job_url}")
        out = requests.get(job_url + "/api/json/", auth=auth, verify=False)
        result = out.json()['result']
        if result:
            # return result
            if result == "SUCCESS":
                output = requests.get(job_url, auth=auth, verify=False)
                for response in output.iter_lines():
                    print(response)
                return result
            else:
                return result
        else:
            logger.info("{}: Status: {}. Polling again in {} secs".format(
                time.ctime(), result, job_poll_interval))
        time.sleep(job_poll_interval)
        job_poll_attempts = job_poll_attempts + 1
    return "Job seems to be stuck as it is not returning the result after 1 hr of time"


if __name__ == "__main__":
    logger.info("Triggering the jenkins job : {}".format(job_name))
    job_info_url = trigger_jenkins_job(jenkins_url, job_name, job_params, auth)
    logger.info("Successfully triggered the jenkins job")
    time.sleep(5)
    logger.info("Trying to capture build info")
    job_url = get_jenkins_job_info(job_info_url)
    logger.info("Successfully captured the build info")
    time.sleep(5)
    logger.info("Trying to capture build status")
    build_status = get_jenkins_job_build(job_url)
    logger.info(build_status)
