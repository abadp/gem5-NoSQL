# Cassandra (nodo-01 --> ycsb, nodo-0x --> cassandra)
./launch_app.sh $num_nodes $app $DB_size $num_threads 
./launch_app-run.sh $num_nodes $app $DB_size $num_threads $app_size
