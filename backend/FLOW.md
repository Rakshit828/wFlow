# Building a Service API Client and Credentials Manager with coordination
1. The credentials manager will be created **internally by Sercvice API Client**
2. The ServiceApiClient should be explicitly created during the workflow execution.



# Service Request Error Handling
We are doing streaming response when we are running a specific workflow. For that we have
to give users track of everything what has happened. (the errors as well)
The errors should be well handled.

First, I have to create base exceptions with proper error classification like:

These all errors occur from the API client. We will create these and raise in ServiceRequestHandler
And, make a decorator for catching these errors and do **Response Formatting** as above.
 
1. Authentication Error (Credentials Related Error)
2. Authorization Error (Permissions related error)
3. Rate Limiting Error
4. ServiceSpecificError(When using specific service like Gmail, Drive from google.)


# Response Sending Format
We will create a certain datamodel which will be returned from the node which should contain every type of response it can return. Eg:

```json
{
    "type": "RESULT" | "ERROR" | "HITL" | "RateLimit" | "STATUS",
    "msg": "Error has occurred sending an email.",
    "meta": {
        // Metadata about the data
    }
}
```

# i AM currently buidlign the config_resolver.