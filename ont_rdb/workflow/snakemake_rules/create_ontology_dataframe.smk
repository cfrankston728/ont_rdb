rule create_ontology_dataframe:
    input:
        ontology_script="ontologies/{ontology_name}_ontology.py"
    output:
        ontology_dataframe="ontology_dataframes/{ontology_name}_ontology_dataframe.pkl"
    params:
        informant_class_path=config['informant_class_path']
    log:
        "logs/{ontology_name}.log"
    conda:
        "envs/environment.yaml"
    shell:
        """
        python3 create_ontology_dataframe.py --inf {params.informant_class_path} --ont {input.ontology_script} --o {output.ontology_dataframe} > {log} 2>&1
        """
