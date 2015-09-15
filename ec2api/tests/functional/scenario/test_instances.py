# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import base64

from oslo_log import log
import six
from tempest_lib.common import ssh
from tempest_lib.common.utils import data_utils
import testtools

from ec2api.tests.functional import base
from ec2api.tests.functional import config
from ec2api.tests.functional.scenario import base as scenario_base

CONF = config.CONF
LOG = log.getLogger(__name__)


class InstancesTest(scenario_base.BaseScenarioTest):

    @testtools.skipUnless(CONF.aws.image_id, "image id is not defined")
    def test_userdata(self):
        key_name = data_utils.rand_name('testkey')
        pkey = self.create_key_pair(key_name)
        sec_group_name = self.create_standard_security_group()
        user_data = six.text_type(data_utils.rand_uuid()) + six.unichr(1071)
        instance_id = self.run_instance(KeyName=key_name, UserData=user_data,
                                        SecurityGroups=[sec_group_name])

        data = self.client.describe_instance_attribute(
            InstanceId=instance_id, Attribute='userData')
        self.assertEqual(data['UserData']['Value'],
            base64.b64encode(user_data.encode("utf-8")).decode("utf-8"))

        ip_address = self.get_instance_ip(instance_id)

        ssh_client = ssh.Client(ip_address, CONF.aws.image_user, pkey=pkey)

        url = 'http://169.254.169.254'
        data = ssh_client.exec_command('curl %s/latest/user-data' % url)
        if isinstance(data, six.binary_type):
            data = data.decode("utf-8")
        self.assertEqual(user_data, data)

        data = ssh_client.exec_command('curl %s/latest/meta-data/ami-id' % url)
        self.assertEqual(CONF.aws.image_id, data)

        data = ssh_client.exec_command(
            'curl %s/latest/meta-data/public-keys/0/' % url)
        self.assertEqual('openssh-key', data)

    @testtools.skipUnless(CONF.aws.image_id, "image id is not defined")
    def test_compare_console_output(self):
        key_name = data_utils.rand_name('testkey')
        pkey = self.create_key_pair(key_name)
        sec_group_name = self.create_standard_security_group()
        instance_id = self.run_instance(KeyName=key_name,
                                        SecurityGroups=[sec_group_name])

        data_to_check = data_utils.rand_uuid()
        ip_address = self.get_instance_ip(instance_id)
        ssh_client = ssh.Client(ip_address, CONF.aws.image_user, pkey=pkey)
        cmd = 'sudo sh -c "echo \\"%s\\" >/dev/console"' % data_to_check
        ssh_client.exec_command(cmd)

        waiter = base.EC2Waiter(self.client.get_console_output)
        waiter.wait_no_exception(InstanceId=instance_id)

        def _compare_console_output():
            data = self.client.get_console_output(InstanceId=instance_id)
            self.assertEqual(instance_id, data['InstanceId'])
            self.assertIsNotNone(data['Timestamp'])
            self.assertIn('Output', data)
            self.assertIn(data_to_check, data['Output'])

        waiter = base.EC2Waiter(_compare_console_output)
        waiter.wait_no_exception()
