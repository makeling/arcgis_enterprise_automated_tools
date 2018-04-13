# -*- coding: UTF-8 -*-
# !/usr/bin/python
# __author__ = 'keling ma'

import os, sys, getopt
import commands
from xml.etree.ElementTree import ElementTree, Element


def main(argv=None):
    opts, args = getopt.getopt(argv, "j:t:w:i:")
    java_jdk_path = "/home/software/jdk-8u151-linux-x64.tar.gz"
    tomcat_path = "/home/software/apache-tomcat-8.0.47.tar.gz"
    webadaptor_path = "/home/software/Web_Adaptor_Java_Linux_106_161911.tar.gz"
    instancename = []

    if len(opts) < 3:
        print("Please input required parameters first!!! \n")
        print('[required] -j : Java jdk path, eg: -j /home/software/jdk-8u151-linux-x64.tar.gz')
        print('[required] -t : Tomcat path, eg: -t /home/software/apache-tomcat-8.0.47.tar.gz')
        print('[required] -w: ArcGIS Web Adaptor path, eg: -w /home/software/Web_Adaptor_Java_Linux_106_161911.tar.gz')
        print("[optional] -i: ArcGIS Web Adaptor instancelist, eg: -i 'portal', 'server'")
        print('\n')
        return

    for op, value in opts:
        if op == "-j":
            java_jdk_path = value
        elif op == "-t":
            tomcat_path = value
        elif op == "-w":
            webadaptor_path = value
        elif op == "-i":
            list_str = value
            instancename = list_str.split(',')



    wa_path, java_home, tomcat_home = unzip_tar_package(tomcat_path,java_jdk_path, webadaptor_path)

    write_java_env_to_profile(java_home)

    war_path = install_webadaptor(wa_path)

    deploy_war_to_tomcat(war_path, tomcat_home, instancename)

    print ('deploy war package successfully!')

    keystore_path = generate_cert_by_keytool(tomcat_home)

    print ("keystore path: ", keystore_path)

    repair_tomcat_config(tomcat_home, keystore_path)

    print ('repair server.xml successfully!')

    start_tomcat(tomcat_home)

    print ('start tomcat successfully!')

    response = validate_install_result()

    print response

    delete_temp_space()

    print ('deploy finished!')

#unzip all the tar package
def unzip_tar_package(tomcat,java, webadaptor):
    print_export_message("Start unzip tar package")
    java_home = ""
    tomcat_home = ""
    commands.getoutput('mkdir /home/temp_unzip')

    commands.getoutput('mkdir /home/webServer')

    tar_webadaptor = 'tar -xvf {1} -C /home/temp_unzip'.replace("{1}", webadaptor)
    commands.getoutput(tar_webadaptor)

    tar_tomcat = 'tar -xvf {1} -C /home/webServer'.replace("{1}", tomcat)
    commands.getoutput(tar_tomcat)

    tar_java = 'tar -xvf {1} -C /home/webServer'.replace("{1}", java)
    commands.getoutput(tar_java)

    wa = commands.getoutput('ls /home/temp_unzip')

    wa_path = os.path.join('/home/temp_unzip', wa)

    ls = commands.getoutput('ls /home/webServer')

    file_list = str(ls).split('\n')

    for file in file_list:
        if file[:1] == 'j':
            java_home =  os.path.join('/home/webServer', file)
        elif file[:1] == 'a' or file[:1] == 't':
            tomcat_home = os.path.join('/home/webServer', file)

    print("Web adaptor install package path: ", wa_path)
    print("Java jdk deploy path: ", java_home)
    print ("Tomcat deploy path: ", tomcat_home)

    return wa_path, java_home, tomcat_home

#write java environment to /etc/profile
def write_java_env_to_profile(java_home):
    print_export_message("Write java environment variable to profile")

    java_home_str = java_home
    commands.getoutput('echo JAVA_HOME={1} >> /etc/profile'.replace("{1}", java_home))

    classpath = ".:" + java_home + "/lib/tools.jar:" + java_home + "/lib/tools.jar "
    commands.getoutput(
        'echo CLASSPATH=.:\$JAVA_HOME/lib/tools.jar:\$JAVA_HOME/lib/tools.jar >> /etc/profile')

    path = "\$JAVA_HOME/bin:\$PATH "
    commands.getoutput('echo PATH=\$JAVA_HOME/bin:\$PATH >> /etc/profile')

    export = "export JAVA_HOME CLASSPATH PATH"
    commands.getoutput('echo export JAVA_HOME CLASSPATH PATH >> /etc/profile')

    print "JAVA_HOME=", java_home
    print "CLASSPATH=", classpath

    os.environ['JAVA_HOME'] = java_home

    os.environ['CLASSPATH'] = classpath

    path = os.environ['PATH']

    os.environ['PATH'] = path + ";" + os.path.join(java_home, 'bin')
    print "PATH=", os.environ['PATH']

#Install ArcGIS Webadaptor
def install_webadaptor(wa_path):
    print_export_message('Start install web adaptor')
    commands.getoutput('mkdir /home/webadaptor')

    cmd = '{1}/Setup -m silent -l yes -d /home/webadaptor'.replace("{1}",wa_path)
    commands.getoutput(cmd)

    print cmd

    w_p = commands.getoutput('ls /home/webadaptor/arcgis')

    war_path = os.path.join('/home/webadaptor/arcgis',w_p, 'java')

    return war_path

#deploy war package to tomcat
def deploy_war_to_tomcat(war_path, tomcat_path, instancename):
    print_export_message('Deploy war package to tomcat')
    war_file = os.path.join(war_path,'arcgis.war')
    tomcat_webapps = os.path.join(tomcat_path, 'webapps')
    if len(instancename) == 0:
        cmd = 'cp -rf ' + war_file + " " + tomcat_webapps
        commands.getoutput(cmd)
        print cmd
    else:
        for instance in instancename:
            instance = instance.strip()
            tomcat_war_path = os.path.join(tomcat_webapps, instance+ ".war")
            cmd = 'cp -rf ' + war_file + " " + tomcat_war_path
            commands.getoutput(cmd)
            print cmd

#generate certificate by keytool
def generate_cert_by_keytool(tomcat_path):

    print_export_message('Generate certificat for enable SSL request')

    hostname = commands.getoutput('hostname -f')
    dname = "\"CN={1}, OU=esrichina, O=esrichina, L=beijing, ST=beijing, C=CN\"".replace("{1}", hostname)

    keytool_cmd01 = "keytool -genkey -alias tomcat -keyalg RSA -keysize 1024 -keystore {2} -validity 36500 -dname {1} -storepass '123456' -keypass '123456'".replace("{1}",dname)

    certs_path = os.path.join(tomcat_path, 'certs')

    commands.getoutput('mkdir ' + certs_path)

    keystore_path = os.path.join(certs_path, 'tomcat.keystore')

    keytool_cmd = keytool_cmd01.replace("{2}", keystore_path)


    print keytool_cmd

    commands.getoutput(keytool_cmd)

    return keystore_path

#repair tomcat server.xml file to enable ssl
def repair_tomcat_config(tomcat_path, keystore_path):
    try:
        print_export_message("Repair server.xml file")
        server_xml_path = os.path.join(tomcat_path,'conf','server.xml')

        tree = read_xml(server_xml_path)

        service_nodes = find_nodes(tree, "Service")

        service_node = get_node_by_key_value(service_nodes, {"name": "Catalina"})

        nodes = find_nodes(tree, "Service/Connector")

        result_nodes = get_node_by_key_value(nodes, {"protocol": "HTTP/1.1"})

        change_node_properties(result_nodes, {"port": "80"})

        change_node_properties(result_nodes, {"redirectPort": "443"})

        ssl_node = get_node_by_key_value(nodes, {"SSLEnabled": "true"})


        if len(ssl_node) == 0:
            new_connector = create_node("Connector", {"SSLEnabled": "true", "URIEncoding": "UTF-8",
                                                      "clientAuth": "false", "connectionTimeout": "20000",
                                                      "connectionUploadTimeout": "3600000", "disableUploadTimeout": "false",
                                                      "keystoreFile": keystore_path,
                                                      "keystorePass": "123456", "maxHttpHeaderSize": "65535",
                                                      "maxPostSize": "10485760", "maxThreads": "150", "port": "443",
                                                      "protocol": "org.apache.coyote.http11.Http11Protocol",
                                                      "scheme": "https", "sslEnabledProtocols": "TLSv1.2,TLSv1.1,TLSv1",
                                                      "secure": "true", "sslProtocol": "TLS"}, "")

            add_child_node(service_node, new_connector)

        write_xml(tree, server_xml_path)
        return True
    except:
        return False

#start tomcat
def start_tomcat(tomcat_path):
    print_export_message('Start tomcat')

    cmd_path = os.path.join(tomcat_path,'bin/startup.sh')

    print cmd_path


    commands.getoutput(cmd_path)

# valiate the install result
def validate_install_result():
    print_export_message('Validate tomcat https request by curl')
    hostname = commands.getoutput('hostname -f')

    cmd = "curl \"https://{1}\" -k".replace("{1}", hostname)

    print cmd

    response = commands.getoutput(cmd)

    return response

# delete temp space
def delete_temp_space():
    commands.getoutput('rm -rf /home/temp_unzip')

#--------------------------------common utils---------------------------------------------------------------------------------------
def print_export_message(content):
    print " "
    presplit = ""
    for i in range(20):
        presplit += '='
    presplit += content

    for i in range(20):
        presplit += "="

    print presplit

#--------------------------------xml decode methods----------------------------------------------------------------------------------
# read xml file
def read_xml(in_path):
    tree = ElementTree()
    tree.parse(in_path)
    return tree

# write xml file
def write_xml(tree, out_path):
    tree.write(out_path, encoding="utf-8", xml_declaration=True)

# check is match
def if_match(node, kv_map):
    for key in kv_map:
        if node.get(key) != kv_map.get(key):
            return False
    return True

# search find nodes
def find_nodes(tree, path):
    return tree.findall(path)

# get node by key value
def get_node_by_key_value(nodelist, kv_map):
    result_nodes = []
    for node in nodelist:
        if if_match(node, kv_map):
            result_nodes.append(node)
    return result_nodes


# update node properties
def change_node_properties(nodelist, kv_map, is_delete=False):
    for node in nodelist:
        for key in kv_map:
            if is_delete:
                if key in node.attrib:
                    del node.attrib[key]
            else:
                node.set(key, kv_map.get(key))

# change node text
def change_node_text(nodelist, text, is_add=False, is_delete=False):
    for node in nodelist:
        if is_add:
            node.text += text
        elif is_delete:
            node.text = ""
        else:
            node.text = text

# create node
def create_node(tag, property_map, content):
    element = Element(tag, property_map)
    element.text = content
    return element

# add child node
def add_child_node(nodelist, element):
    for node in nodelist:
        node.insert(1, element)

# delete node by tag, key, value
def del_node_by_tag_key_value(nodelist, tag, kv_map):
    for parent_node in nodelist:
        children = parent_node.getchildren()
        for child in children:
            if child.tag == tag and if_match(child, kv_map):
                parent_node.remove(child)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
