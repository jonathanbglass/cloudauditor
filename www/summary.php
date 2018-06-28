<?php 
include 'common.php';
$order_by = "al_account_id asc";
$dbconn = getdb();
$sql = "SELECT * from view_al_status order by " . $order_by;
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
if (isset($_GET['output']) && $_GET['output'] == 'json') {
  header("Content-type: application/json");
  header("Content-Disposition: attachment; filename=alertlogic_install_stats.json");
  header("Pragma: no-cache");
  header("Expires: 0");
  $jsonoutput= "[";
  foreach ($resarray as $key=>$val) {
    $jsonoutput .=  "{\"al_account_id\": " . $resarray[$key]['al_account_id'] . "," . 
                    "\"aws_account_id\": " . $resarray[$key]['aws_account_id'] . "," .
                    "\"al_account_name\": \"" . $resarray[$key]['al_account_name'] . "\"," .
                    "\"api_key\": \"" .  $resarray[$key]['api_key'] . "\"},";
  }
  $jsonoutput = substr_replace($jsonoutput, '', -1);
  $jsonoutput .= "]";
  print $jsonoutput;
  die();
}
if (isset($_GET['output']) && $_GET['output'] == 'csv') {
  header("Content-type: text/csv");
  header("Content-Disposition: attachment; filename=alertlogic_install_stats.csv");
  header("Pragma: no-cache");
  header("Expires: 0");
  print "aws_account_id,alertlogic_account_id,account_name,aws_instance_count,aws_vpc_count,al_threatmanager_protected_hosts,al_threatmanager_visible_hosts,al_threatmanager_appliance_count,insert_date\n";
  foreach ($resarray as $key=>$val) {
    $line = "\"" . sprintf("%'012d", $resarray[$key]['aws_account_id']) . "\",";
    $line .= $resarray[$key]['al_account_id'] . ",";
    $line .= "\"" . $resarray[$key]['account_name'] . "\",";
    $line .= $resarray[$key]['instance_counts'] . ",";
    $line .= $resarray[$key]['aws_vpcs'] . ",";
    $line .= $resarray[$key]['tm_protected_hosts_count'] . ",";
    $line .= $resarray[$key]['tm_hosts_count'] . ",";
    $line .= $resarray[$key]['tm_appliance_count'] . ",";
    $line .= $resarray[$key]['insert_ts'] . "\n";
    print $line;
  }
  die();
} 
$title="ISO - Alert Logic Deployments - Executive Summary";
generate_head($title);
$arrow = "arrow_drop_up";
$c1value = "col_1_asc";
$c2value = "col_2_asc";
$c3value = "col_3_asc";
$c4value = "col_4_asc";
$c5value = "col_5_asc";
$c6value = "col_6_asc";
$c7value = "col_7_asc";
$c8value = "col_8_asc";
if (isset($_POST['orderby'])) {
  switch ($_POST['orderby']) {
    case "col_1_asc":
      $arrow = "arrow_drop_up";
      $c1value = "col_1_desc";
      $order_by = "aws_account_id asc";
      break;
    case "col_1_desc":
      $arrow = "arrow_drop_down";
      $c1value = "col_1_asc";
      $order_by = "aws_account_id desc";
      break;
    case "col_2_asc":
      $arrow = "arrow_drop_up";
      $c2value = "col_2_desc";
      $order_by = "al_account_id asc";
      break;
    case "col_2_desc":
      $arrow = "arrow_drop_down";
      $c2value = "col_2_asc";
      $order_by = "al_account_id desc";
      break;
    case "col_3_asc":
      $arrow = "arrow_drop_up";
      $c3value = "col_3_desc";
      $order_by = "account_name asc";
      break;
    case "col_3_desc":
      $arrow = "arrow_drop_down";
      $c3value = "col_3_asc";
      $order_by = "account_name desc";
      break;
    case "col_4_asc":
      $arrow = "arrow_drop_up";
      $c4value = "col_4_desc";
      $order_by = "instance_counts asc";
      break;
    case "col_4_desc":
      $arrow = "arrow_drop_down";
      $c4value = "col_4_asc";
      $order_by = "instance_counts desc";
      break;
    case "col_5_asc":
      $arrow = "arrow_drop_up";
      $c5value = "col_5_desc";
      $order_by = "aws_vpcs asc";
      break;
    case "col_5_desc":
      $arrow = "arrow_drop_down";
      $c5value = "col_5_asc";
      $order_by = "aws_vpcs desc";
      break;
    case "col_6_asc":
      $arrow = "arrow_drop_up";
      $c6value = "col_6_desc";
      $order_by = "tm_protected_hosts_count asc";
      break;
    case "col_6_desc":
      $arrow = "arrow_drop_down";
      $c6value = "col_6_asc";
      $order_by = "tm_protected_hosts_count desc";
      break;
    case "col_7_asc":
      $arrow = "arrow_drop_up";
      $c7value = "col_7_desc";
      $order_by = "tm_hosts_count asc";
      break;
    case "col_7_desc":
      $arrow = "arrow_drop_down";
      $c7value = "col_7_asc";
      $order_by = "tm_hosts_count desc";
      break;
    case "col_8_asc":
      $arrow = "arrow_drop_up";
      $c8value = "col_8_desc";
      $order_by = "tm_appliance_count asc";
      break;
    case "col_8_desc":
      $arrow = "arrow_drop_down";
      $c8value = "col_8_asc";
      $order_by = "tm_appliance_count desc";
      break;
  }
}

$sql = "SELECT * from view_al_install_summary";
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
?>
<link href="/css/c3.css" rel="stylesheet" type="text/css">
<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="/css/c3.min.js"></script>
<script src="/js/timeseries.js" async></script>
<body>
<div style="overflow-x:auto;">
  <table>
    <tr>
      <th colspan=2>Alert Logic Threat Manager</th>
    </tr>
    <tr>
      <td colspan=2 bgcolor=black></td>
    </tr>
    <tr>
      <th>Protected Hosts</th>
      <td align=right><?php print $resarray[0]['TM Protected Host Count']; ?></td>
    </tr>
    <tr>
      <th>AWS Instances</th>
      <td align=right><?php print $resarray[0]['AWS Instances'];?></td>
    </tr>
    <tr>
      <th>Agent Percent Installed</th>
      <td align=right><?php print round($resarray[0]['Percent Agent Installed'],2);?>%</td>
    </tr>
    <tr>
      <td colspan=2 bgcolor=black></td>
    </tr>
    <tr>
      <th>Appliance Installs</th>
      <td align=right><?php print $resarray[0]['TM Appliance Count'];?></td>
    </tr>
    <tr>
      <th>AWS VPCs</th>
      <td align=right><?php print $resarray[0]['AWS VPCs'];?></td>
    </tr>
    <tr>
      <th>Appliance Install Percentage</th>
      <td align=right><?php print round($resarray[0]['Percent Appliances Installed'],2);?>%</td>
    </tr>
  </table>
<p align=center>
<div style="overflow-x:auto;">
  <table>
    <tr>
      <td colspan=8 align=right style="font-size:12px;vertical-align:middle;"><a href="<?php print $_SERVER['PHP_SELF'];?>?output=csv"><i>Download As CSV</i><i class="material-icons" style="font-size:12px;color:blue;vertical-align:middle;">file_download</i></a></td>
    <tr>
      <th>AWS</th>
      <th colspan=2>Alert Logic</th>
      <th colspan=2>AWS</th>
      <th colspan=3>Threat Manager Counts</th>
    </tr>
    <tr valign=bottom>
      <th onclick="submitform('postdata1')">
        Account # 
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_1_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_1_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata1" method="post">
        <input type="hidden" name="orderby" value="<?php print $c1value;?>"/>
        </form></th>
      <th onclick="submitform('postdata2')">
      Account # 
<?php 
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_2_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_2_asc') { print "<i class=\"material-icons\">$arrow</i>"; }
} else { print "<i class=\"material-icons\">arrow_drop_up</i>";}?>
        <form action="" name="postdata2" method="post">
        <input type="hidden" name="orderby" value="<?php print $c2value;?>"/>
        </form></th>
      <th onclick="submitform('postdata3')">
        Account Name 
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_3_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_3_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata3" method="post">
        <input type="hidden" name="orderby" value="<?php print $c3value;?>"/>
        </form></th>
      <th onclick="submitform('postdata4')">
      Instances
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_4_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_4_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata4" method="post">
        <input type="hidden" name="orderby" value="<?php print $c4value;?>"/>
        </form></th>
      <th onclick="submitform('postdata5')">
      VPCs
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_5_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_5_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata5" method="post">
        <input type="hidden" name="orderby" value="<?php print $c5value;?>"/>
        </form></th>
      <th onclick="submitform('postdata6')">
      Protected<br>Hosts
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_6_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_6_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata6" method="post">
        <input type="hidden" name="orderby" value="<?php print $c6value;?>"/>
        </form></th>
      <th onclick="submitform('postdata7')">
      Hosts
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_7_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_7_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata7" method="post">
        <input type="hidden" name="orderby" value="<?php print $c7value;?>"/>
        </form></th>
      <th onclick="submitform('postdata8')">
      Appliance
<?php
if (isset($_POST['orderby'])) {
  if ($_POST['orderby'] == 'col_8_desc') { print "<i class=\"material-icons\">$arrow</i>"; }
  if ($_POST['orderby'] == 'col_8_asc') { print "<i class=\"material-icons\">$arrow</i>"; } } ?>
        <form action="" name="postdata8" method="post">
        <input type="hidden" name="orderby" value="<?php print $c8value;?>"/>
        </form></th>
    </tr>
<?php
$date_collected = $resarray[0]['date_collected'];
$sql = "SELECT * from view_al_status order by " . $order_by;
$res = pg_query($dbconn, $sql);
$resarray = pg_fetch_all($res);
foreach ($resarray as $key=>$val) {
  print '    <tr>' . "\n";
  print '      <td>' . sprintf("%'012d\n", $resarray[$key]['aws_account_id'])  . "</td>\n";
  print '      <td align=center>' . $resarray[$key]['al_account_id']  . "</td>\n";
  print '      <td>' . $resarray[$key]['account_name']  . "</td>\n";
  print '      <td align=right>' . $resarray[$key]['instance_counts']  . "</td>\n";
  print '      <td align=right>' . $resarray[$key]['aws_vpcs']  . "</td>\n";
  print '      <td align=right>' . $resarray[$key]['tm_protected_hosts_count']  . "</td>\n";
  print '      <td align=right>' . $resarray[$key]['tm_hosts_count']  . "</td>\n";
  print '      <td align=right>' . $resarray[$key]['tm_appliance_count']  . "</td>\n";
  print "    </tr>\n";
}
?>
   </table>
</div>
<div id="footer" align=center>
Data Collected: <?php print $date_collected ;?>
<p>
Data Classification: Company Confidential
</div>
<div id="chart"></div>
  </body>
  </html>
