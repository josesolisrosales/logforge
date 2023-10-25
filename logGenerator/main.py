import datetime as dt
import random
import os
import json

defaultLogDays = 7
defaultLogIntervalSeconds = 5
defaultRandomLogTimestampShift = True
defaultLogLevels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
defaultLogLevelFrecuencyDistribution = {"INFO": "0.85", "WARNING": "0.148", "ERROR": "0.0018", "CRITICAL": "0.0002"}
defaultLogLevelMessage = {
        "INFO": "This is an info message",
        "DEBUG": "This is a debug message",
        "WARNING": "This is a warning message",
        "ERROR": "This is an error message",
        "CRITICAL": "This is a critical message"
    }
defaultGeneratedLogsOutputFilePath = "sample-logs.txt"

def randomLogLevelGenerator(LogLevels, FrecuencyDistribution):
    """
    This function returns a random log level based on a frecuency distribution.
    """

    frecuencies = [float(frecuency) for frecuency in FrecuencyDistribution.values()]

    totalFrequency = sum(frecuencies)

    # Clamps the values so the sum of all frequencies is 1
    normalizedFrequencies = [frecuency / totalFrequency for frecuency in frecuencies]

    randomNumber = random.random()

    cumulativeFrequency = 0
    for index, frecuency in enumerate(normalizedFrequencies):
        cumulativeFrequency += frecuency
        if randomNumber < cumulativeFrequency:
            return LogLevels[index]

    raise ValueError("Invalid frequency distribution")


def formatLogMessage(timestamp, logLevel, logMessage, logStartChart='{', logEndChar='}', delimiter='-'):
    """
    This function returns a formatted log message.
    """

    timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")


    return f"{logStartChart}\"{timestamp}\" {delimiter} \"{logLevel}\" {delimiter} \"{logMessage}\"{logEndChar}"


def generateRandomIntervals(startTime, endTime, n):
    intervals = []

    # Calculate the total time span in hours
    totalHours = (endTime - startTime).total_seconds() / 3600

    # Generate n random intervals
    for _ in range(n):
        # Randomly select a starting point within the total time span
        randomStart = random.uniform(0, totalHours) * 3600  # Convert back to seconds
        startInterval = startTime + timedelta(seconds=randomStart)

        # Calculate the end of the 1-hour interval
        endInterval = startInterval + timedelta(hours=1)

        intervals.append((startInterval, endInterval))

    return intervals


def generateLogSample(logStartTimestamp, logEndTimestamp, logIntervalSeconds, randomLogTimestampShift, logLevels, logLevelFrecuencyDistribution, standardErrorMessage, outputFilePath):

    generatedLogLines = []

    while logStartTimestamp < logEndTimestamp:

        logLevel = randomLogLevelGenerator(logLevels, logLevelFrecuencyDistribution)

        if randomLogTimestampShift:
            randomTimestampShift = dt.timedelta(seconds=random.randint(0, logIntervalSeconds))
        else:
            randomTimestampShift = dt.timedelta(seconds=0)

        logObject = {"timestamp": logStartTimestamp + randomTimestampShift, "logLevel": logLevel, "logMessage": standardErrorMessage[logLevel]}
        generatedLogLines.append(logObject)

        logStartTimestamp += dt.timedelta(seconds=logIntervalSeconds)

    if outputFilePath:
        with open(outputFilePath, "w") as outputFile:
            for logObject in generatedLogLines:
                outputFile.write(formatLogMessage(timestamp=logObject["timestamp"], logLevel=logObject["logLevel"], logMessage=logObject["logMessage"]) + "\n")
        return True

    return False


def clearConsole():
    os.system("cls" if os.name == "nt" else "clear")


def enterToContinue(message="Press enter to continue..."):
    input(message)


def loadConfigFromFile(configFilePath):
    print(f"Attempting to load config from {configFilePath}")

    try:
        with open(configFilePath, "r") as configFile:
            config = json.load(configFile)
    except FileNotFoundError:
        print("Config file not found. Using default config.")
        return defaultLogDays, defaultLogIntervalSeconds, defaultRandomLogTimestampShift, defaultLogLevels, defaultLogLevelFrecuencyDistribution, defaultLogLevelMessage, defaultGeneratedLogsOutputFilePath

    logDays = config["logDays"] if "logDays" in config else defaultLogDays
    logIntervalSeconds = config["logIntervalSeconds"] if "logIntervalSeconds" in config else defaultLogIntervalSeconds
    randomLogTimestampShift = config["randomLogTimestampShift"] if "randomLogTimestampShift" in config else defaultRandomLogTimestampShift
    logLevels = config["logLevels"] if "logLevels" in config else defaultLogLevels
    logLevelFrecuencyDistribution = config["logLevelFrecuencyDistribution"] if "logLevelFrecuencyDistribution" in config else defaultLogLevelFrecuencyDistribution
    logLevelMessage = config["logLevelMessage"] if "logLevelMessage" in config else defaultLogLevelMessage
    generatedLogsOutputFilePath = config["generatedLogsOutputFilePath"] if "generatedLogsOutputFilePath" in config else defaultGeneratedLogsOutputFilePath

    enterToContinue("Config loaded successfully. Press enter to continue...")

    return logDays, logIntervalSeconds, randomLogTimestampShift, logLevels, logLevelFrecuencyDistribution, logLevelMessage, generatedLogsOutputFilePath


def main():
    clearConsole()
    print("Welcome to the log generator!")
    configFilePath = input("Please enter the path to the config file (leave empty for default config): ")

    clearConsole()
    logDays, logIntervalSeconds, randomLogTimestampShift, logLevels, logLevelDistribution, logLevelMessage, generatedLogsOutputFilePath = loadConfigFromFile(configFilePath)

    logStartTimestamp = dt.datetime.now() - dt.timedelta(days=logDays)
    logEndTimestamp = dt.datetime.now()

    clearConsole()
    print("Generating log sample...")

    logsGenerated = generateLogSample(logStartTimestamp=logStartTimestamp,
                      logEndTimestamp=logEndTimestamp,
                      logIntervalSeconds=logIntervalSeconds,
                      randomLogTimestampShift=randomLogTimestampShift,
                      logLevels=logLevels,
                      logLevelFrecuencyDistribution=logLevelDistribution,
                      standardErrorMessage=logLevelMessage,
                      outputFilePath=generatedLogsOutputFilePath)

    if logsGenerated:
        print("Log sample generated successfully!")
    else:
        print("Error generating log sample")


if __name__ == '__main__':
    main()
