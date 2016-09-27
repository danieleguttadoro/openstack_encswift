# == Class: swift
#

class swift
{
  $source = 'https://github.com/danieleguttadoro/ovencswiftserver_onthefly.git'
  $devstack_dir = '/home/stack/devstack'
  $swift_dir = '/home/stack/swift'
  $user = $user::stack::username
  $branch = 'barbican'

  exec { 'swift_clone':
    require => [
      File['/usr/local/bin/git_clone.sh'],
      Exec['devstack_clone'],
    ],
    path => '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:.',
    environment => "HOME=/home/$user",
    user => 'stack',
    group => 'stack',
    command => "/usr/local/bin/git_clone.sh ${source} ${branch} ${swift_dir}",
    logoutput => true,
    timeout => 1200,
  }

  exec { 'to_exec_command-git.sh':
    require => [
        Exec['swift_clone'],
    ],
    path => '/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:.',
    user => 'stack',
    environment => "HOME=/home/$user",
    group => 'stack',
    command => "bash -c 'sudo chmod +x /opt/stack/swift/swift/usr/command-git.sh",
    logoutput => true,
    timeout => 1200, 
    returns => 2, 
  }

}
