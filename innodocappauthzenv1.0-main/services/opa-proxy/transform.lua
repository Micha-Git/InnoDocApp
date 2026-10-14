package.cpath = package.cpath .. ";/usr/lib/x86_64-linux-gnu/lua/5.1/?.so;/usr/lib/x86_64-linux-gnu/lua/5.2/?.so"
package.cpath = package.cpath .. ";/usr/lib/aarch64-linux-gnu/lua/5.1/?.so;/usr/lib/aarch64-linux-gnu/lua/5.2/?.so"
package.cpath = package.cpath .. ";/usr/lib/arm-linux-gnueabihf/lua/5.1/?.so;/usr/lib/arm-linux-gnueabihf/lua/5.2/?.so"
package.path = package.path .. ";/usr/share/lua/5.1/?.lua;/usr/share/lua/5.1/?/init.lua;/usr/share/lua/5.2/?.lua"

local ok, cjson = pcall(require, "cjson")
if not ok then
    cjson = nil
end
-- Wrap JSON body into { input = <decoded> } unless already wrapped
local function wrap_input_json(raw)
    if cjson == nil then
        return nil
    end
    local ok, obj = pcall(cjson.decode, raw)
    if not ok or obj == nil then
        return nil
    end
    if type(obj) ~= "table" then
        return nil
    end
    if obj.input ~= nil then
        return nil
    end
    local wrapped = {
        input = obj
    }
    local ok2, encoded = pcall(cjson.encode, wrapped)
    if not ok2 then
        return nil
    end
    return encoded
end

-- Unwrap to inner result: prefer response.result, else result
local function unwrap_result_json(raw)
    if cjson == nil then
        return nil
    end
    local ok, obj = pcall(cjson.decode, raw)
    if not ok or obj == nil then
        return nil
    end
    if type(obj) ~= "table" then
        return nil
    end
    local inner = nil
    if type(obj.response) == "table" and obj.response.result ~= nil then
        inner = obj.response.result.result
    elseif obj.result ~= nil then
        inner = obj.result.result
    else
        return nil
    end

    local ok2, encoded = pcall(cjson.encode, inner)
    if not ok2 then
        return nil
    end
    return encoded
end

function envoy_on_request(handle)
    local body = handle:body()
    if body == nil then
        return
    end

    local length = body:length()
    if not length or length == 0 then
        return
    end

    local raw = body:getBytes(0, length)
    if raw == nil or raw == "" then
        return
    end

    local new_body = wrap_input_json(raw)
    if new_body == nil then
        return
    end

    body:setBytes(new_body)

    local headers = handle:headers()
    headers:remove("accept-encoding")
    headers:replace("content-type", "application/json")
    headers:replace("content-length", tostring(#new_body))
end

function envoy_on_response(handle)
    local body = handle:body()
    if body == nil then
        return
    end

    local length = body:length()
    if not length or length == 0 then
        return
    end

    local raw = body:getBytes(0, length)
    if raw == nil or raw == "" then
        return
    end

    local new_body = unwrap_result_json(raw)
    if new_body == nil then
        return
    end

    body:setBytes(new_body)

    local headers = handle:headers()
    headers:replace("content-type", "application/json")
    headers:replace("content-length", tostring(#new_body))
end
