<?php 
include 'common.php';
$title="ISO IAM Auditor - AWS Accounts";
generate_head($title);
$order_by = "aws_account_id asc";
$c1value = "col_1_asc";
$c2value = "col_2_asc";
if (isset($_POST['orderby'])) { 
  print ($_POST['orderby']);
  switch ($_POST['orderby']) {
  case "col_1_asc":
    $c1value = "col_1_desc";
    $order_by = "aws_account_id asc";
    break;
  case "col_1_desc":
    $c1value = "col_1_asc";
    $order_by = "aws_account_id desc";
    break;
  case "col_2_asc":    
    $c2value = "col_2_desc";
    $order_by = "aws_account_name asc";
    break;
  case "col_2_desc":    
    $c2value = "col_2_asc";
    $order_by = "aws_account_name desc";
    break;
  }
}
$dbconn = getdb();
$account_sql = "SELECT * from aws_accounts ORDER BY " . $order_by;
$account_res = pg_query($dbconn, $account_sql);
$account_res_array = pg_fetch_all($account_res);
if (is_array($account_res_array)) {
?>
<div class="flex-container">
<header>
  <h1>Turner AWS Accounts and Contacts</h1>
</header>
<article class="article">
<div style="overflow-x:auto;">
  <table>
    <tr>
      <th onclick="submitform('postdata1')">
        AWS<br>Account #
        <form action="" name="postdata1" method="post">
        <input type="hidden" name="orderby" value="<?php print $c1value;?>"/>
        </form></th>
      <th onclick="submitform('postdata2')">
      Account Name
        <form action="" name="postdata2" method="post">
        <input type="hidden" name="orderby" value="<?php print $c2value;?>"/>
        </form></th>
      <th>Account<br>Active</th>
      <th>MSS COPS<br>Root Access</th>
      <th>Invoice Approver</th>
      <th>Operational Contact</th>
      <th>Security Contact</th>
    </tr>
<?php
foreach ($account_res_array as $key=>$val) {
  // this part creates the first 4 columns of the table; will always be the same
  print '    <tr>' . "\n";
  print '      <td>' . str_pad($account_res_array[$key]['aws_account_id'], 12, "0", STR_PAD_LEFT)  . "</td>\n";
  print '      <td>' . $account_res_array[$key]['aws_account_name']  . "</td>\n";
  $account_active_bool = ($account_res_array[$key]['account_active']=="t" ? "True" : "False");
  print '      <td>' . $account_active_bool  . "</td>\n";
  $mss_cops_root_bool= ($account_res_array[$key]['mss_cops_root_access']=="t" ? "True" : "False");
  print '      <td>' . $mss_cops_root_bool  . "</td>\n";
  $invoice_approver_td  = "      <td>";
  $op_contact_td        = "      <td>";
  $security_contact_td  = "      <td>";
  $roles_sql = "SELECT * from aws_account_roles WHERE aws_account_id = " . $account_res_array[$key]['aws_account_id'] . " ORDER BY aws_account_id";
  $roles_res = pg_query($dbconn, $roles_sql);
  $roles_res_array = pg_fetch_all($roles_res);
  if (is_array($roles_res_array)) { // check to make sure pgsql returned results
    foreach ($roles_res_array as $rolekey=>$roleval) {
      // sub loop
      // this part should build table cells for each role until the next account number
      // set variables
      $aws_account_id = $account_res_array[$key]['aws_account_id'];
      $roles_acct_id = $roles_res_array[$rolekey]['aws_account_id'];
      $roles_role = $roles_res_array[$rolekey]['account_role'];
      $roles_email= strtolower($roles_res_array[$rolekey]['email_address']);
      if ($roles_acct_id === $aws_account_id ) {
        switch ($roles_role) {
        case "Invoice Approver":
          // make sure this person is not already in this table cell
          $blah = strpos(strtolower($invoice_approver_td), $roles_email);
          if ($blah == FALSE) { 
            $invoice_approver_td .= $roles_email . "<br>";
//            print "<!-- DEBUG: Adding $roles_email to INVOICE APPROVER | $blah | -->\n";
          }
          break;
        case "Operational Contact":
          // make sure this person is not already in this table cell
          $blah = strpos(strtolower($op_contact_td), $roles_email);
          if ($blah == FALSE) { 
            $op_contact_td .= $roles_email . "<br>";
//            print "<!-- DEBUG: Adding $roles_email to OPERATIONAL CONTACT | $blah |  -->\n";
          }
          break;
        case "Security Contact":
          // make sure this person is not already in this table cell
          $blah = strpos(strtolower($security_contact_td), $roles_email); 
          if ($blah == FALSE) { 
            $security_contact_td .= $roles_email . "<br>";
//            print "<!-- DEBUG: Adding $roles_email to SECURITY CONTACT | $blah | -->\n";
          }
          break;
        } // end switch statement
      } // end if 
    } // end sub loop 
  } // end if (is_array)

  $invoice_approver_td  .= "      </td>\n";
  $op_contact_td        .= "      </td>\n";
  $security_contact_td  .= "      </td>\n";
  print $invoice_approver_td;
  print $op_contact_td;
  print $security_contact_td;
  unset ($invoice_approver_td);
  unset ($op_contact_td);
  unset ($security_contact_td);
  print "    </tr>\n";
}
print "   </table>
  </article>
<footer>Turner Confidential</footer>
";
}
generate_footer();
