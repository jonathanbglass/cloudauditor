<?php
// Initialize session
session_start();

function authenticate($user, $password) {
	if(empty($user) || empty($password)) return false;

	// Active Directory server
	$ldap_host = "server.college.school.edu";

	// Active Directory DN
	$ldap_dn = "OU=Departments,DC=college,DC=school,DC=edu";

	// Active Directory user group
	$ldap_user_group = "WebUsers";

	// Active Directory manager group
	$ldap_manager_group = "WebManagers";

	// Domain, for purposes of constructing $user
	$ldap_usr_dom = '@college.school.edu';

	// connect to active directory
	$ldap = ldap_connect($ldap_host);

	// verify user and password
	if($bind = @ldap_bind($ldap, $user.$ldap_usr_dom, $password)) {
		// valid
		// check presence in groups
		$filter = "(sAMAccountName=".$user.")";
		$attr = array("memberof");
		$result = ldap_search($ldap, $ldap_dn, $filter, $attr) or exit("Unable to search LDAP server");
		$entries = ldap_get_entries($ldap, $result);
		ldap_unbind($ldap);

		// check groups
		foreach($entries[0]['memberof'] as $grps) {
			// is manager, break loop
			if(strpos($grps, $ldap_manager_group)) { $access = 2; break; }

			// is user
			if(strpos($grps, $ldap_user_group)) $access = 1;
		}

		if($access != 0) {
			// establish session variables
			$_SESSION['user'] = $user;
			$_SESSION['access'] = $access;
			return true;
		} else {
			// user has no rights
			return false;
		}

	} else {
		// invalid name or password
		return false;
	}
}
?>