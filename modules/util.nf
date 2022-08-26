def print_logo(){

    println("")
    println("  __________  ___   ________________          ")
    println(""" /_  __/ __ \\/   | / ____/ ____/ __ \\_  __    """)
    println("  / / / /_/ / /| |/ /   / __/ / /_/ / |/_/    ")
    println(" / / / _, _/ ___ / /___/ /___/ _, _/>  <      ")
    println("/_/ /_/_|_/_/ _|_\\____/_____/_/_|_/_/|_|      ")
    println("   / __ \\/ / / / /   / ____/ |/ /             ")
    println("  / /_/ / /_/ / /   / __/  |   /              ")
    println(" / ____/ __  / /___/ /___ /   |               ")
    println("/_/   /_/ /_/_____/_____//_/|_|               ")    
    println("")
    println("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    println("~~~~~~ Multiplex Imaging Pipeline ~~~~~~~")
    println("~~~~~~~~~ Part I: Deep-imcyto ~~~~~~~~~~~")
    println("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    println("")

}

def check_params() {
    println("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
    println "\nExecuting pipeline with the following parameters:"
    params.each{ k, v -> println "params.${k.padRight(25)} = ${v}" }
    println("\n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n")

}