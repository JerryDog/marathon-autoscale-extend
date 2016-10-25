Usage: marathon_autoscale.py [options]

Options:
  -h, --help            show this help message and exit
  -H HOST, --host=HOST  Hostname or IP of your Marathon Instance
  -A APP, --app=APP     The Marathon Application Name
  -M MEMORY, --memory=MEMORY
                        The Max percent of Mem Usage averaged across all
                        Application Instances to trigger Autoscale (ie. 80)
  -C CPU, --cpu=CPU     The Max percent of CPU Usage averaged across all
                        Application Instances to trigger Autoscale (ie. 80)
  -T TRIGGER, --trigger=TRIGGER
                        Which metric(s) to trigger Autoscale ('and', 'or')
  -S SCALE, --scale=SCALE
                        Autoscale multiplier for triggered Autoscale (ie 1.5)
  -X MAX_INSTANCES, --max_instances=MAX_INSTANCES
                        The Max instances that should ever exist for this
                        application (ie. 20)
  -x MIN_INSTANCES, --min_instances=MIN_INSTANCES
                        The Min instances that should ever exist for this
                        application (ie. 2)
  -N NUMBER_OF_OVER_TIMES, --number_of_over_times=NUMBER_OF_OVER_TIMES
                        Number of over threshold, then trigger to scale(ie. 5)


功能：
连续N次超过阈值，扩容
连续N次低于5%，缩容

ex:
docker run -it --rm --name my-running-script \
 -v "$PWD":/usr/src/myapp -w /usr/src/myapp \
 python3 python3 marathon_autoscale.py -H 10.43.1.190 -A test -M 50 -C 20 -T or -S 1.5 -X 10 -x 2 -N 5

或者将该脚本做入容器，直接后台运行，原始镜像为 frolvlad/alpine-python3