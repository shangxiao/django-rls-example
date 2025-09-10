# django-rls-example

Postgres Row Level Security: https://www.postgresql.org/docs/current/ddl-rowsecurity.html#DDL-ROWSECURITY

Some notes:

 - Tables must have row level security enabled & a policy created
 - RLS doesn't apply to roles with superuser
 - RLS only applies to roles for their own tables if RLS is "forced"

Possible approach this PoC is exploring:

 - Have 2 database connections in settings:
   - First: a superuser (or someone with create table permission) for migrations
   - Second: a standard app user who hasn't created the table and is not a superuser
 - 2 separate connections may not be necessary if the same user is not a superuser but has enough privileges to setup the database, however RLS must be forced
 - Examples show authorisation through custom parameter but similar approach can be done with roles & the `currentuser` identifier
   - The roles will need to be added/removed upon user management
   - The standard app user will need permissin to SET ROLE
 - Setting parameters isn't 100% secure imho as there's always the potential to "leak"
   - Roles are designed to be tied to connections whereas webapps reuse connections (or transactions)
   - Setting a parameter works in the same way as their lifetime is defined either by:
     - Session; or
     - Transaction
   - Setting a param or role within a session has no way of automatically resetting or expiring meaning that if you use this approach the application
     has to reset/clear it.  Bugs in code will mean users potentially seeing someone else's data.
   - Similarly for setting params/roles in a transaction.
   - The only way to automatically clear a param/role for a webapp with long-living connections appears to be:
     - Only set params/roles in a transaction
     - Only allow a single setting
     - Therefore wrapping any DB access with a transaction which may not be ideal for high volume
