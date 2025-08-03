def filter_commands(args, supported_commands):
    matches = []
    tips=supported_commands
    pargs=args
    pargs_size=len(args)
    dtips=tips.copy()
    deep=0
    while deep<pargs_size:
        if not (
            isinstance(dtips, str)
            or isinstance(dtips, list)
            or isinstance(dtips, dict)
        ):
            matches = []
            break
        if isinstance(dtips, str) and pargs[deep] in dtips:
            # str
            matches.append(dtips)
            break
        elif pargs[deep] in dtips:
            matches.append(pargs[deep])
            if isinstance(dtips,dict):
                dtips=dtips[pargs[deep]]
            elif isinstance(dtips,list):
                dtips=dtips[dtips.index(pargs[deep])]
        else:
            if isinstance(dtips,dict):
                matches=dtips.keys()
            elif isinstance(dtips,list):
                matches=dtips
            break
        deep+=1
    if deep+1!=pargs_size:
        matches= []
    return matches

# 示例用法
if __name__ == "__main__":
    args = ["cmd2", "subcmd2", "param"]
    args = ["cmd2", "subcmd3", "param"]
    # args = ["cmd1", "param"]
    
    supported_commands = {
        "cmd1": ["param1", "param2", "param3"],
        "cmd2": {
            "subcmd1": ["paramA", "paramB"],
            "subcmd2": ["paramX", "paramY"],
            "subcmd3":'paramZ'
        }
    }
    
    result = filter_commands(args, supported_commands)
    print("Filtered commands:", result)