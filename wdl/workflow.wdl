# Example workflow
# Declare WDL version 1.0 if working in Terra
version 1.0

workflow myWorkflow {
    input {
        File to_print
        String to_save
    }

    call myTask {
        input: s = to_print, o = to_save
    }
}

task myTask {
    input {
        File s
        String o
    }

    command <<<
        cat ~{s} >> ~{o}
    >>>

    output {
        File out = o
    }
}