__author__ = 'liujiahua'

import sys
import requests
import json
import math
import time
from optparse import OptionParser
parser = OptionParser()

"""
marathon_host = input("Enter the DNS hostname or IP of your Marathon Instance : ")
marathon_app = input("Enter the Marathon Application Name to Configure Autoscale for from the Marathon UI : ")
max_mem_percent = int(input("Enter the Max percent of Mem Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : "))
max_cpu_time = int(input("Enter the Max percent of CPU Usage averaged across all Application Instances to trigger Autoscale (ie. 80) : "))
trigger_mode = input("Enter which metric(s) to trigger Autoscale ('and', 'or') : ")
autoscale_multiplier = float(input("Enter Autoscale multiplier for triggered Autoscale (ie 1.5) : "))
max_instances = int(input("Enter the Max instances that should ever exist for this application (ie. 20) : "))
"""

parser.add_option("-H", "--host", dest="host",
                  help="Hostname or IP of your Marathon Instance")

parser.add_option("-A", "--app", dest="app",
                  help="The Marathon Application Name")

parser.add_option("-M", "--memory", dest="memory",
                  help="The Max percent of Mem Usage averaged across all "
                       "Application Instances to trigger Autoscale (ie. 80)")

parser.add_option("-C", "--cpu", dest="cpu",
                  help="The Max percent of CPU Usage averaged across all "
                       "Application Instances to trigger Autoscale (ie. 80)")

parser.add_option("-T", "--trigger", dest="trigger",
                  help="Which metric(s) to trigger Autoscale ('and', 'or')")

parser.add_option("-S", "--scale", dest="scale",
                  help="Autoscale multiplier for triggered Autoscale (ie 1.5)")

parser.add_option("-X", "--max_instances", dest="max_instances",
                  help="The Max instances that should ever exist for this application (ie. 20)")

parser.add_option("-x", "--min_instances", dest="min_instances",
                  help="The Min instances that should ever exist for this application (ie. 2)")

parser.add_option("-N", "--number_of_over_times", dest="number_of_over_times",
                  help="Number of over threshold, then trigger to scale(ie. 5)")

(options, args) = parser.parse_args()

marathon_host = options.host
marathon_app = options.app
max_mem_percent = int(options.memory)
max_cpu_time = int(options.cpu)
trigger_mode = options.trigger
autoscale_multiplier = float(options.scale)
max_instances = int(options.max_instances)
min_instances = int(options.min_instances)
number_of_over_times = int(options.number_of_over_times)

# over threshold times, default 0
OVER_TIMES = 0

# below  threshold times
BELOW_TIMES = 0

# normal threshold percent, if instances > min_instances, need to scale down
normal_cpu_percent = 5
normal_mem_percent = 5


class Marathon(object):

    def __init__(self, marathon_host):
        self.name = marathon_host
        self.uri=("http://"+marathon_host+":8080")

    def get_all_apps(self):
        response = requests.get(self.uri + '/v2/apps').json()
        if response['apps'] == []:
            print ("No Apps found on Marathon")
            sys.exit(1)
        else:
            apps=[]
            for i in response['apps']:
                appid = i['id'].strip('/')
                apps.append(appid)
            print ("Found the following App LIST on Marathon =", apps)
            self.apps = apps # TODO: declare self.apps = [] on top and delete this line, leave the apps.append(appid)
            return apps

    def get_app_details(self, marathon_app):
        response = requests.get(self.uri + '/v2/apps/'+ marathon_app).json()
        if (response['app']['tasks'] ==[]):
            print ('No task data on Marathon for App !', marathon_app)
        else:
            app_instances = response['app']['instances']
            self.appinstances = app_instances
            print(marathon_app, "has", self.appinstances, "deployed instances")
            app_task_dict={}
            for i in response['app']['tasks']:
                taskid = i['id']
                hostid = i['host']
                print ('DEBUG - taskId=', taskid +' running on '+hostid)
                app_task_dict[str(taskid)] = str(hostid)
            return app_task_dict

    def scale_app(self,marathon_app,autoscale_multiplier):
        target_instances_float=self.appinstances * autoscale_multiplier
        target_instances=math.ceil(target_instances_float)
        if (target_instances > max_instances):
            print("Reached the set maximum instances of", max_instances)
            target_instances=max_instances
        else:
            target_instances=target_instances
        data ={'instances': target_instances}
        json_data=json.dumps(data)
        headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/v2/apps/'+ marathon_app,json_data,headers=headers)
        print ('Scale_app return status code =', response.status_code)

    def scale_down_app(self,marathon_app,autoscale_multiplier):
        if self.appinstances == min_instances:
            print("Already the minimum instances, do nothing.")
            return
        target_instances_float=self.appinstances / autoscale_multiplier
        target_instances=int(target_instances_float)
        if (target_instances < min_instances):
            print("Reached the set minimum instances of", min_instances)
            target_instances=min_instances
        else:
            target_instances=target_instances
        data ={'instances': target_instances}
        json_data=json.dumps(data)
        headers = {'Content-type': 'application/json'}
        response=requests.put(self.uri + '/v2/apps/'+ marathon_app,json_data,headers=headers)
        print ('Scale_down_app return status code =', response.status_code)


def get_task_agentstatistics(task, host):
    # Get the performance Metrics for all the tasks for the Marathon App specified
    # by connecting to the Mesos Agent and then making a REST call against Mesos statistics
    # Return to Statistics for the specific task for the marathon_app
    response = requests.get('http://'+host + ':5051/monitor/statistics.json').json()
    #print ('DEBUG -- Getting Mesos Metrics for Mesos Agent =',host)
    for i in response:
        executor_id = i['executor_id']
        #print("DEBUG -- Printing each Executor ID ", executor_id)
        if (executor_id == task):
            task_stats = i['statistics']
            # print ('****Specific stats for task',executor_id,'=',task_stats)
            return task_stats


def timer():
    print("Successfully completed a cycle, sleeping for 30 seconds ...")
    time.sleep(30)
    return


if __name__ == "__main__":
    print("This application tested with Python3 only")
    running = 1
    while running == 1:
        # Initialize the Marathon object
        aws_marathon = Marathon(marathon_host)
        # Call get_all_apps method for new object created from aws_marathon class and return all apps
        marathon_apps = aws_marathon.get_all_apps()
        print ("The following apps exist in Marathon...", marathon_apps)
        # Quick sanity check to test for apps existence in MArathon.
        if (marathon_app in marathon_apps):
            print ("  Found your Marathon App=", marathon_app)
        else:
            print ("  Could not find your App =", marathon_app)
            sys.exit(1)
        # Return a dictionary comprised of the target app taskId and hostId.
        app_task_dict = aws_marathon.get_app_details(marathon_app)
        print ("    Marathon  App 'tasks' for", marathon_app, "are=", app_task_dict)

        app_cpu_values = []
        app_mem_values = []
        for task,host in app_task_dict.items():
            #cpus_time =(task_stats['cpus_system_time_secs']+task_stats['cpus_user_time_secs'])
            #print ("Combined Task CPU Kernel and User Time for task", task, "=", cpus_time)

            # Compute CPU usage
            task_stats = get_task_agentstatistics(task, host)
            cpus_system_time_secs0 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs0 = float(task_stats['cpus_user_time_secs'])
            timestamp0 = float(task_stats['timestamp'])

            time.sleep(1)

            task_stats = get_task_agentstatistics(task, host)
            cpus_system_time_secs1 = float(task_stats['cpus_system_time_secs'])
            cpus_user_time_secs1 = float(task_stats['cpus_user_time_secs'])
            timestamp1 = float(task_stats['timestamp'])

            cpus_time_total0 = cpus_system_time_secs0 + cpus_user_time_secs0
            cpus_time_total1 = cpus_system_time_secs1 + cpus_user_time_secs1
            cpus_time_delta = cpus_time_total1 - cpus_time_total0
            timestamp_delta = timestamp1 - timestamp0

            # CPU percentage usage
            usage = float(cpus_time_delta / timestamp_delta) * 100

            # RAM usage
            mem_rss_bytes = int(task_stats['mem_rss_bytes'])
            print ("task", task, "mem_rss_bytes=", mem_rss_bytes)
            mem_limit_bytes = int(task_stats['mem_limit_bytes'])
            print ("task", task, "mem_limit_bytes=", mem_limit_bytes)
            mem_utilization = 100 * (float(mem_rss_bytes) / float(mem_limit_bytes))
            print ("task", task, "mem Utilization=", mem_utilization)
            print()

            #app_cpu_values.append(cpus_time)
            app_cpu_values.append(usage)
            app_mem_values.append(mem_utilization)
        # Normalized data for all tasks into a single value by averaging
        app_avg_cpu = (sum(app_cpu_values) / len(app_cpu_values))
        print ('Current Average  CPU Time for app', marathon_app, '=', app_avg_cpu)
        app_avg_mem=(sum(app_mem_values) / len(app_mem_values))
        print ('Current Average Mem Utilization for app', marathon_app,'=', app_avg_mem)
        #Evaluate whether an autoscale trigger is called for
        if BELOW_TIMES > 1000:
            BELOW_TIMES = 0  # reset below times
        print('\n')
        if (trigger_mode == "and"):
            if (app_avg_cpu > max_cpu_time) and (app_avg_mem > max_mem_percent):
                OVER_TIMES += 1
                BELOW_TIMES = 0  # below times reset to 0
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold. Over Times: %s" % OVER_TIMES)
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold. Below Times reset to 0")
                if (OVER_TIMES % number_of_over_times == 0):
                    print ("Start Autoscale...")
                    aws_marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                OVER_TIMES = 0 # over times reset to 0
                if (OVER_TIMES ==0) and (app_avg_cpu < normal_cpu_percent) and (app_avg_mem < normal_mem_percent):
                    BELOW_TIMES += 1
                print ("Both values were not greater than autoscale targets. Over Times reset to 0")
                print ("Both values were not greater than autoscale targets. Below Times--: %s" % BELOW_TIMES)
                if (BELOW_TIMES > 0) and (BELOW_TIMES % number_of_over_times == 0):
                    print ("Start Autoscale Down...(If already is min instance, do nothing)")
                    aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
        elif (trigger_mode == "or"):
            if (app_avg_cpu > max_cpu_time) or (app_avg_mem > max_mem_percent):
                OVER_TIMES += 1
                BELOW_TIMES = 0  # below times reset to 0
                print ("Autoscale triggered based Mem 'or' CPU exceeding threshold. Over Times: %s" % OVER_TIMES)
                print ("Autoscale triggered based on 'both' Mem & CPU exceeding threshold. Below Times reset to 0")
                if (OVER_TIMES % number_of_over_times == 0):
                    print ("Start Autoscale...")
                    aws_marathon.scale_app(marathon_app, autoscale_multiplier)
            else:
                OVER_TIMES = 0 # over times reset to 0
                if (OVER_TIMES ==0) and (app_avg_cpu < normal_cpu_percent) and (app_avg_mem < normal_mem_percent):
                    BELOW_TIMES += 1
                print ("Both values were not greater than autoscale targets. Over Times reset to 0")
                print ("Neither Mem 'or' CPU values exceeding threshold. Below Times--: %s" % BELOW_TIMES)
                if (BELOW_TIMES > 0) and (BELOW_TIMES % number_of_over_times == 0):
                    print ("Start Autoscale Down...(If already is min instance, do nothing)")
                    aws_marathon.scale_down_app(marathon_app, autoscale_multiplier)
        timer()