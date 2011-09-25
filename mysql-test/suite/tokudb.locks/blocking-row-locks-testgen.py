# 9/23/2011 Generate blocking row lock tests
import datetime

# whether or not to do a sleep hack to get
# tests to pass
do_sleep_hack = False

# generate sql write queries
def mysqlgen_select_for_update(k, kv, c, cv):
    print "select * from t where %s=%s for update;" % (k, kv)
def mysqlgen_select_for_update_range(k, c, where):
    print "select * from t where %s%s for update;" % (k, where)
def mysqlgen_update(k, kv, c, cv):
    print "update t set %s=%s where %s=%s;" % (c, c, k, kv);
def mysqlgen_update_range(k, c, where):
    print "update t set %s=%s where %s%s;" % (c, c, k, where);
def mysqlgen_insert_ignore(k, kv, c, cv):
    print "insert ignore t values(%s, %s);" % (kv, cv)
def mysqlgen_insert_on_dup_update(k, kv, c, cv):
    print "insert t values(%s, %s) on duplicate key update %s=%s;" % (kv, cv, c, c)
def mysqlgen_replace(k, kv, c, cv):
    print "replace t values(%s, %s);" % (kv, cv)

# genrate sql read queries
def mysqlgen_select_star():
    print "select * from t;"
def mysqlgen_select_where(k, where):
    print "select * from t where %s%s;" % (k, where)

# mysql test code generation
def mysqlgen_prepare():
    print "# prepare with some common parameters"
    print "set storage_engine=tokudb;"
    #print "connect(conn1, localhost, root);"
    #print "set autocommit=off;"
    print "connect(conn2, localhost, root);"
    print "connection default;"
    print ""
def mysqlgen_reload_table():
    print "# drop old table, generate new one. 4 rows"
    print "--disable_warnings"
    print "drop table if exists t;"
    print "--enable_warnings"
    print "create table t (a int primary key, b int);"
    for i in range(1, 7):
        mysqlgen_insert_ignore("a", i, "b", i*i)
    print ""
def mysqlgen_cleanup():
    print "# clean it all up"
    print "drop table t;"
    print "set global tokudb_lock_timeout=30000000;"
    print ""
write_point_queries = [
        ("select for update", mysqlgen_select_for_update),
        ("update", mysqlgen_update),
        ("insert", mysqlgen_insert_ignore),
        ("replace", mysqlgen_replace) ]
write_range_queries = [
        ("select for update", mysqlgen_select_for_update_range),
        ("update", mysqlgen_update_range) ]

# Here's where all the magic happens
print "# Tokutek"
print "# Blocking row lock tests;"
print "# Generated by %s on %s;" % (__file__, datetime.date.today())
print ""
mysqlgen_prepare()
mysqlgen_reload_table()
for timeout in ["0", "1000000"]:
    print "# testing with timeout %s" % timeout
    print "set global tokudb_lock_timeout=%s;" % timeout
    print ""
    print "# testing each point query vs each point query"
    for ta, qa in write_point_queries:
        # point vs point contention
        for tb, qb in write_point_queries:
            print "# testing conflict \"%s\" vs. \"%s\"" % (ta, tb)
            print "connection default;"
            print "begin;"
            print ""
            qa("a", "1", "b", "100")
            print "connection conn2;"
            for k in range(1, 5):
                if k == 1:
                    print "--error ER_LOCK_WAIT_TIMEOUT"
                if do_sleep_hack:
                    print "--sleep 0.2"
                qb("a", k, "b", "100")
            # Always check in the end that a commit
            # allows the other transaction full access
            print "connection default;"
            print "commit;"
            print "connection conn2;"
            qb("a", "1", "b", "100")
            mysqlgen_select_star()
            print "connection default;"
            print ""
        # point vs range contention
        for rt, rq in write_range_queries:
            print "# testing range query \"%s\" vs \"%s\"" % (rt, ta)
            print "connection default;"
            print "begin;"
            print ""
            qa("a", "1", "b", "100")
            print "connection conn2;"
            print "--error ER_LOCK_WAIT_TIMEOUT"
            if do_sleep_hack:
                print "--sleep 0.2"
            rq("a", "b", "<=2")
            print "--error ER_LOCK_WAIT_TIMEOUT"
            if do_sleep_hack:
                print "--sleep 0.2"
            rq("a", "b", ">=0")
            rq("a", "b", ">2")
            # Always check in the end that a commit
            # allows the other transaction full access
            print "connection default;"
            print "commit;"
            print "connection conn2;"
            rq("a", "b", "<=2")
            rq("a", "b", ">=0")
            mysqlgen_select_star()
            print "connection default;"
            print ""
    for rt, rq in write_range_queries:
        for rtb, rqb in write_range_queries:
            print "# testing range query \"%s\" vs range query \"%s\"" % (rt, rtb)
            print "connection default;"
            print "begin;"
            print ""
            rq("a", "b", ">=2 and a<=4")
            print "connection conn2;"
            print "--error ER_LOCK_WAIT_TIMEOUT"
            rqb("a", "b", ">=0 and a<=3")
            print "--error ER_LOCK_WAIT_TIMEOUT"
            rqb("a", "b", ">=3 and a<=6")
            print "--error ER_LOCK_WAIT_TIMEOUT"
            rqb("a", "b", "<=2")
            rqb("a", "b", ">=5")
            # Always check in the end that a commit
            # allows the other transaction full access
            print "connection default;"
            print "commit;"
            print "connection conn2;"
            rqb("a", "b", ">=0 and a<=3")
            rqb("a", "b", ">=3 and a<=6")
            rqb("a", "b", "<=2")
            mysqlgen_select_star()
            print "connection default;"
            print ""
mysqlgen_cleanup()
