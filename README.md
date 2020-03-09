# SkilletLoader

Example scripts and Dockerfile to load Skillets via a CI/CD pipeline



## Example Jenkinsfile

Here is an example jenkins script that will load a skillet as a stage of your deployment pipeline

```
pipeline {
    agent {
        docker {
            // https://github.com/nembery/SkilletLoader
            image "nembery/skilletloader:dev"
            alwaysPull true
        }
    }
    environment {
        // Grab our lab rats IP and auth information from the credentials store
        PANOS_IP        = credentials("PANOS_LAB_RAT_IP")
        PANOS_AUTH      = credentials('PANOS_LAB_RAT_AUTH')
        PANOS_GW        = credentials('PANOS_LAB_RAT_GW')
        PANOS_MASK      = credentials('PANOS_MASK')

        // Grab our auth code to ensure the FW is fully licensed
        AUTH_CODE      = credentials('VM50_AUTH_CODE')
        // Any variables from the skillet definition will be overridden with values from the environment
        // for this test, we will override the FW_NAME var and network information vars
        FW_NAME         = "test-${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
        ADMINISTRATOR_USERNAME  = "${PANOS_AUTH_USR}"
        ADMINISTRATOR_PASSWORD  = "${PANOS_AUTH_PSW}"
        MGMT_TYPE               = "static"
        MGMT_IP                 = "${PANOS_IP}"
        MGMT_MASK               = "${PANOS_MASK}"
        MGMT_DG                 = "${PANOS_GW}"
    }

    stages {
        stage('Load IronSkillet PAN-OS Snippets') {
            steps {
                echo "Baseline configuration is now complete"
                // load_skillet takes a relative path to a skillet to load
                // skillet variables can be overridden in the environment
                sh 'load_skillet.py ./templates/panos/snippets -i ${PANOS_IP} -u ${PANOS_AUTH_USR} -p ${PANOS_AUTH_PSW}'
            }
        }
    }
    post {
        success {
            echo 'Skillet Loaded Successfully'
        }
        failure {
            echo 'Could not preform load of Skillet'
        }
        always {
            echo "Build complete"
        }
    }
}


```