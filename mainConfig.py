from netmiko import Netmiko
import re
import pandas as pd
from jinja2 import Environment, FileSystemLoader
from yaml import safe_load
import concurrent.futures



def device_processin():
    prompt = "[+] This script merely understand Excel extension files, "
    prompt += "\nplease enter the excel file that contains the devices you want to make connections to"
    print(prompt)

    filepath01 = input("File name: ")
    if filepath01:
        extension = 'xlsx'
        pattern = r'[\w\.-_]+\.' + extension + '$'
        try:
            if re.match(pattern, filepath01):
                df = pd.read_excel(filepath01)
                df.drop(columns=['Unnamed: 0'], inplace=True)
                devicesList = df.to_dict(orient='records')
            else:
                return "[!] The script could not understand the file extension."
        except Exception as e:
            print(e)
        else:
            return devicesList
    else:
        print("[!] File name must not be empty.")


def jinja_config_template():
    env = Environment(loader=FileSystemLoader("templates"))
    template01 = env.get_template("template02.txt")

    file_name = "config02.yml"
    with open(file_name, "r") as rObject:
        data01 = safe_load(rObject)
        # print(data01)

    result = template01.render(data01)

    parsed_result = {}
    current_entry = None

    for line in result.split("\n"):
        host_match = re.match(r'hostname (.+)', line)
        int_match = re.match(r'interface (.+)', line)
        no_switch = re.match(r'no (.+)', line)
        ip_addr = re.match(r'ip address (.+)', line)
        descr_match = re.match(r'description (.+)', line)
        # no_shut_cmd = 'no shutdown'
        
        if host_match:
            current_entry = host_match.group(1)
            parsed_result[current_entry] = []
            parsed_result[current_entry].append(host_match.group())
        elif int_match:
            parsed_result[current_entry].append(int_match.group())
        elif no_switch:
            parsed_result[current_entry].append(no_switch.group())
        elif ip_addr:
            parsed_result[current_entry].append(ip_addr.group())
        elif descr_match:
            parsed_result[current_entry].append(descr_match.group())
        # elif no_shut_cmd:
            # parsed_result[current_entry].append(no_shut_cmd)
    
    return parsed_result


def session_establish(host, cmd):
    # deviceList = device_processin()
    # commands2run = jinja_config_template()
    # print(commands2run)
    try:
      # for host, cmd in zip(deviceList, commands2run.values()):
      print(f"\n**** Connecting to {host['host']} ****")
      net_connect = Netmiko(**host)
      net_connect.enable()
        # print(cmd)

      output = net_connect.send_config_set(cmd)
    except:
      print(f"\n**** Can not login to {host['host']} ****")
    else:
      print(output)




def ssh_thread():
  deviceList = device_processin()
  commands2run = jinja_config_template()
  results = []
        
  if deviceList is not None and commands2run is not None:
      with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(session_establish, host, cmd) for host, cmd in zip(deviceList, commands2run.values())]
            
        for future in concurrent.futures.as_completed(futures):
          result = future.result()
          if result:
            results.append(result)
      print(results)
